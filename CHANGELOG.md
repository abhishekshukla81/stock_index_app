# Change Log

Original function `fetch_global_stocks` reviewed and refactored into `stock_universe.py`, plus a web app.

## Bug fixes

| # | Issue | Fix |
|---|---|---|
| 1 | S&P 500 filter `isalpha() or "-" in sym and sym != "CASH"` had an operator-precedence bug, so `CASH`/`USD` leaked in. | Shared `_us_tickers()` excludes `CASH`/`USD` and validates with a regex (`AAPL`, `BRK-B`). |
| 2 | NASDAQ 100 filter used `isalpha()` after `.`->`-`, which dropped valid class-share tickers. | Same `_us_tickers()` is used for both US indices. |
| 3 | Unknown "NIFTY ..." names silently returned NIFTY 500. | Strict alias lookup. Unknown names raise `UnsupportedIndexError`. |
| 4 | `DPW.DE` is outdated (Deutsche Post is now DHL Group). | Replaced with `DHL.DE`. |
| 5 | Errors and unsupported indices both returned `[]`. | `UnsupportedIndexError` and `DataSourceError` are separate. The API returns 400 and 502. |
| 6 | `except Exception` hid the cause. | Catches `RequestException`, `KeyError`, `ValueError` and `ImportError`. Details are logged, and the client gets a generic message. |
| 7 | Misleading "verified/official" messages. | Removed. Static lists are labelled as snapshots. |
| 8 | **Found in live testing:** the Invesco `holdings-0.csv` URL now returns an HTML page (HTTP 200), so NASDAQ 100 failed to parse. | Switched to Invesco's JSON holdings API and kept only `Common Stock` and ADR rows. This drops futures, currency and cash rows. |

## Breakout scanner and React UI

* `scanner.py` runs the CAR + 30/50/200 DMA breakout scan (with 52-week closing high and its date) in a background thread per index. See the `/api/scan` endpoints in `app.py`.
* The UI is a React 19 + Vite app in `frontend/`. Flask serves the built bundle from `frontend/dist` and keeps the same CSP (scripts and styles from `self` only).

## How to run

Locally:

    cd stock_index_app               # run everything below from inside this folder
    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
    (cd frontend && npm ci && npm run build)   # build the React UI once
    .venv/bin/python app.py          # http://127.0.0.1:5000
    .venv/bin/python -m pytest -q    # offline tests

UI development with hot reload (Flask on :5000 in another terminal):

    cd frontend && npm run dev       # http://127.0.0.1:5173, /api is proxied to Flask

Google Colab: build `frontend/dist` locally first and upload the whole folder (Colab has no Node by default), then:

    %cd stock_index_app
    !pip install -q -r requirements.txt
    %run colab_run.py
