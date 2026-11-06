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

## How to run

Locally:

    cd stock_index_app               # run everything below from inside this folder
    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
    .venv/bin/python app.py          # http://127.0.0.1:5000
    .venv/bin/python -m pytest -q    # 10 offline tests

Google Colab: upload the `stock_index_app` folder, then run in cells:

    %cd stock_index_app
    !pip install -q -r requirements.txt
    %run colab_run.py                # prints a proxied URL to open

Live check (6 Nov 2026): S&P 500 returned 503 tickers, NASDAQ 100 returned 101 (GOOGL and GOOG both listed), and NIFTY 50 returned 50. NIFTY 100/200/500/Midcap 150 and the SSGA/Invesco layouts were not exercised beyond that.

## Improvements

- `print` replaced with `logging`.
- Duplicate tickers removed (`dict.fromkeys`).
- Empty results raise an error.
- 10 MB download cap.
- Honest `User-Agent` (no browser spoofing).
- Output tickers are validated against an allowlist regex. This blocks CSV formula injection (`=cmd|...`) in exports.
- Download helper and alias table de-duplicated.

## New: web application (`app.py`)

- Flask UI: pick an index, then **Load** shows the table and **Export CSV** downloads it.
- API: `GET /api/indices`, `/api/constituents?index=`, `/api/export?index=`.
- One-hour in-memory cache.
- Binds to `127.0.0.1` only.
- CSP, nosniff and no-referrer headers.
- The UI uses `textContent` only (no `innerHTML`).
- Generic error messages.
- `colab_run.py` runs it in Colab through the built-in port proxy.

## Known limitations

- DAX 40 and ISEQ 20 are static snapshots. ISEQ has 16 entries, not 20. Check both against the current composition.
- Upstream URLs and layouts (SSGA `skiprows=4`, `Ticker`/`Symbol` columns) can change without notice.
- Check each provider's terms before redistributing data.
- Dependencies are pinned in `requirements.txt`. Run a vulnerability scan (Mend) in CI.
