# Breakout Scanner - GitHub Pages edition (static)

Same scan and same look as the Flask app in the repo root, but with **no server**.
A GitHub Action runs the scan on a schedule and publishes the results as static files.

## How it differs from the Flask app

| | Flask app (repo root) | Pages app (`pages_app/`) |
|---|---|---|
| Where it runs | Your machine / a server | GitHub (Actions + Pages), public URL |
| Scan trigger | On demand, when you pick an index | Scheduled: weekdays 22:30 UTC, or the manual "Run workflow" button |
| Data freshness | Live (minutes) | Daily snapshot; the page shows the scan time |
| Index switch | Starts a scan (seconds to minutes) | Instant (reads a JSON file) |
| Backend / secrets | Python server | None. Static files only |
| Excel export | Generated per request | Pre-built `.xlsx` per index |
| Cost | Hosting if public | Free |

## Layout

    pages_app/generate.py        scans every index -> JSON + XLSX + manifest.json
    pages_app/web/               React + Vite UI (reads data/*.json)
    pages_app/web/public/data    generated data, committed by the workflow
    pages_app/requirements.txt   Python deps for the workflow
    .github/workflows/pages.yml  schedule, build, deploy

`generate.py` reuses `scanner.py` and `stock_universe.py` from the repo root, so both apps
share one scan logic.

## Publish on GitHub

1. Push this repository to GitHub.
2. **Settings -> Pages -> Build and deployment -> Source: GitHub Actions.**
3. **Settings -> Actions -> General -> Workflow permissions: Read and write.**
4. Run the workflow once: **Actions -> Breakout Scanner (GitHub Pages) -> Run workflow**.
5. The site is at `https://<user>.github.io/<repo>/`.

A push to `main` that touches `pages_app/` rebuilds the site from the data already in the repo
(no Yahoo calls). Scheduled and manual runs refresh the data first.

## Run locally

    pip install -r pages_app/requirements.txt
    python pages_app/generate.py --out pages_app/web/public/data --only "DAX 40"   # or omit --only
    cd pages_app/web && npm ci && npm run dev      # http://127.0.0.1:5174

A full scan of all indices takes about 3 minutes.

## Safeguards

* An index is only published if at least 80% of its tickers returned prices. Otherwise the
  previous file is kept and marked `stale`, and the page says so. This prevents a Yahoo rate
  limit from showing a false "0 breakouts".
* The job fails only if no index could be produced at all.

## Known limitation

ISEQ 20 is not published: 6 of its 16 hard-coded tickers (`AIBG.IR`, `RY4C.IR`, `FBD.IR`,
`DHG.IR`, `GVP.IR`, `UN0.IR`) return no data from Yahoo Finance, so it fails the 80% check.
The list in `stock_universe.py` is a static snapshot and needs updating. This also affects the
Flask app, which silently skips those tickers.

## Notes

* GitHub pauses scheduled workflows after 60 days without repository activity; the
  data-refresh commits count as activity.
* Data may be delayed or incomplete. Not investment advice.
