"""Generate static scan results for the GitHub Pages app.

Runs the breakout scan for every supported index and writes JSON files that the
React UI reads directly (no backend needed):

    <out>/manifest.json        index list + generation time
    <out>/<slug>.json          one file per index
    <out>/<slug>.xlsx          the same results as an Excel file

Usage:
    python pages_app/generate.py --out pages_app/web/public/data
    python pages_app/generate.py --out ... --only "DAX 40" "ISEQ 20"
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

import scanner  # noqa: E402
from stock_universe import (  # noqa: E402
    DataSourceError,
    fetch_global_stocks,
    supported_indices,
)

logger = logging.getLogger("generate")

# Refuse to publish an index if fewer than this share of tickers returned data
# (guards against Yahoo rate limiting producing a misleading "0 breakouts").
MIN_COVERAGE = 0.8


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def scan_index(name, today=None):
    """Return the result dict for one index, or raise DataSourceError."""
    tickers = fetch_global_stocks(name)
    stats = {}
    df = scanner.scan(tickers, today=today, stats=stats)
    missing = stats.get("missing", [])
    coverage = 1 - len(missing) / len(tickers)
    if coverage < MIN_COVERAGE:
        raise DataSourceError(
            f"{name}: only {coverage:.0%} of tickers returned prices"
        )
    return {
        "index": name,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total": len(tickers),
        "no_data": len(missing),
        "count": len(df),
        "rows": df.to_dict(orient="records"),
    }


def write_xlsx(path, rows):
    pd.DataFrame(rows, columns=scanner.COLUMNS).to_excel(path, index=False)


def write_json(path, data):
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, type=Path, help="output directory")
    ap.add_argument("--only", nargs="*", help="limit to these canonical index names")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("stock_universe").setLevel(logging.WARNING)

    names = args.only or supported_indices()
    unknown = [n for n in names if n not in supported_indices()]
    if unknown:
        ap.error(f"unsupported index: {unknown}")

    args.out.mkdir(parents=True, exist_ok=True)
    manifest = {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "indices": []}
    failed = []

    for name in names:
        file = f"{slug(name)}.json"
        try:
            result = scan_index(name)
            write_json(args.out / file, result)
            write_xlsx(args.out / file.replace(".json", ".xlsx"), result["rows"])
            logger.info("%s: %d breakouts of %d", name, result["count"], result["total"])
        except Exception as exc:
            # Keep the previous file for this index (if any) rather than publishing bad data.
            logger.error("%s failed: %s", name, type(exc).__name__)
            failed.append(name)
            if not (args.out / file).is_file():
                continue
            result = json.loads((args.out / file).read_text(encoding="utf-8"))
            result["stale"] = True
            write_json(args.out / file, result)
        manifest["indices"].append(
            {"name": name, "file": file, "xlsx": file.replace(".json", ".xlsx"), "count": result["count"], "total": result["total"],
             "generated_at": result["generated_at"], "stale": bool(result.get("stale"))}
        )

    write_json(args.out / "manifest.json", manifest)
    if failed:
        logger.warning("Failed (kept previous data where available): %s", failed)
    # Fail the job only if nothing at all could be produced.
    return 0 if manifest["indices"] else 1


if __name__ == "__main__":
    sys.exit(main())
