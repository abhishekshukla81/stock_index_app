"""Flask web UI + JSON/CSV API for stock_universe. Binds to 127.0.0.1 only."""

import csv
import io
import logging
import secrets
import threading
import time
from datetime import datetime

import pandas as pd
from flask import Flask, Response, jsonify, render_template, request

import scanner
from stock_universe import (
    DataSourceError,
    UnsupportedIndexError,
    fetch_global_stocks,
    resolve_index,
    supported_indices,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

CACHE_TTL = 3600  # seconds
_cache = {}
_cache_lock = threading.Lock()


def get_tickers(index_name):
    """Fetch tickers with a small in-memory TTL cache keyed by canonical name."""
    key = resolve_index(index_name)
    now = time.time()
    with _cache_lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < CACHE_TTL:
            return key, hit[1]
    tickers = fetch_global_stocks(key)
    with _cache_lock:
        _cache[key] = (now, tickers)
    return key, tickers


# ---- Background breakout scans -------------------------------------------
SCAN_TTL = 3600  # reuse a finished scan for this long
MAX_JOBS = 50
_jobs = {}  # job_id -> dict
_jobs_by_index = {}  # canonical index -> job_id (latest)
_jobs_lock = threading.Lock()


def _run_scan(job_id, index):
    job = _jobs[job_id]
    try:
        _, tickers = get_tickers(index)
        job["total"] = len(tickers)

        def progress(done, total):
            job["done"] = done

        df = scanner.scan(tickers, progress=progress)
        job["rows"] = df.to_dict(orient="records")
        job["state"] = "done"
    except Exception:
        logger.error("Scan failed for %s", index, exc_info=True)
        job["state"] = "error"
    finally:
        job["finished"] = time.time()


def _start_scan(index):
    """Return (job_id, job); reuses a running/fresh job for the same index."""
    with _jobs_lock:
        job_id = _jobs_by_index.get(index)
        job = _jobs.get(job_id)
        if job and (
            job["state"] == "running"
            or (job["state"] == "done" and time.time() - job["finished"] < SCAN_TTL)
        ):
            return job_id, job
        # Evict oldest finished jobs to bound memory.
        while len(_jobs) >= MAX_JOBS:
            finished = [k for k, v in _jobs.items() if v["state"] != "running"]
            if not finished:
                break
            oldest = min(finished, key=lambda k: _jobs[k]["finished"])
            _jobs.pop(oldest)
        job_id = secrets.token_urlsafe(16)
        job = {
            "index": index, "state": "running", "done": 0, "total": 0,
            "rows": [], "started": time.time(), "finished": 0.0,
        }
        _jobs[job_id] = job
        _jobs_by_index[index] = job_id
    threading.Thread(target=_run_scan, args=(job_id, index), daemon=True).start()
    return job_id, job


def _job_view(job_id, job):
    return {
        "job_id": job_id, "index": job["index"], "state": job["state"],
        "done": job["done"], "total": job["total"],
        "count": len(job["rows"]),
        "rows": job["rows"] if job["state"] == "done" else [],
    }


@app.after_request
def security_headers(resp):
    resp.headers["Content-Security-Policy"] = (
        "default-src 'none'; script-src 'self'; style-src 'self'; "
        "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'"
    )
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    return resp


def _load_or_error():
    index = request.args.get("index", "", type=str)[:50]
    try:
        return get_tickers(index), None
    except UnsupportedIndexError:
        return None, (jsonify(error="Unsupported index"), 400)
    except DataSourceError:
        return None, (jsonify(error="Could not load data for this index"), 502)


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/indices")
def api_indices():
    return jsonify(indices=supported_indices())


@app.get("/api/constituents")
def api_constituents():
    result, err = _load_or_error()
    if err:
        return err
    name, tickers = result
    return jsonify(index=name, count=len(tickers), tickers=tickers)


@app.get("/api/export")
def api_export():
    result, err = _load_or_error()
    if err:
        return err
    name, tickers = result
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["index", "ticker"])
    writer.writerows((name, t) for t in tickers)
    filename = "".join(c if c.isalnum() else "_" for c in name).lower() + "_constituents.csv"
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/scan")
def api_scan_start():
    index = request.args.get("index", "", type=str)[:50]
    try:
        canonical = resolve_index(index)
    except UnsupportedIndexError:
        return jsonify(error="Unsupported index"), 400
    job_id, job = _start_scan(canonical)
    return jsonify(_job_view(job_id, job)), 202


@app.get("/api/scan/<job_id>")
def api_scan_status(job_id):
    job = _jobs.get(job_id[:64])
    if not job:
        return jsonify(error="Unknown scan"), 404
    return jsonify(_job_view(job_id, job))


@app.get("/api/scan/<job_id>/export")
def api_scan_export(job_id):
    job = _jobs.get(job_id[:64])
    if not job:
        return jsonify(error="Unknown scan"), 404
    if job["state"] != "done":
        return jsonify(error="Scan not finished"), 409
    buf = io.BytesIO()
    pd.DataFrame(job["rows"], columns=scanner.COLUMNS).to_excel(buf, index=False)
    safe = "".join(c if c.isalnum() else "_" for c in job["index"]).strip("_")
    filename = f"Breakout_{safe}_{datetime.now().strftime('%d-%m-%Y')}.xlsx"
    return Response(
        buf.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
