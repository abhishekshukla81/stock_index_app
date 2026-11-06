# Breakout Scanner

Web app that scans a stock index for **positive breakouts**: the close is above the 30, 50 and 200 day moving averages, and the CAR (cumulative average of closes since the 52-week closing high) has risen for the last 10 sessions. Results include the 52-week closing high and the date it occurred, and can be exported to Excel.

- Backend: Python / Flask (`app.py`, `scanner.py`, `stock_universe.py`)
- Frontend: React 19 + Vite (`frontend/`), served by Flask after a build
- Supported indices: S&P 500, NASDAQ 100, DAX 40, ISEQ 20, NIFTY 50 / 100 / 200 / 500 / MIDCAP 150

The server binds to `127.0.0.1` only. It is not reachable from other machines.

## Prerequisites

| Tool | Minimum version | Why |
|---|---|---|
| Python | 3.12 | Flask, pandas, yfinance backend |
| Node.js | 20.19 or 22.12+ (LTS recommended) | Builds the React UI (includes `npm`) |
| Git | any recent | Clone the repository |
| Internet access | | Index constituents and Yahoo Finance prices |

Install them for your OS, then verify:

```bash
python3 --version   # Windows: py --version
node --version
npm --version
git --version
```

### Fedora

```bash
sudo dnf install -y python3 python3-pip nodejs npm git
```

Check `node --version` is 20.19 or newer. If your release ships an older Node, install a newer stream (for example `sudo dnf module list nodejs`) or use [nvm](https://github.com/nvm-sh/nvm).

### macOS

Install [Homebrew](https://brew.sh) if you don't have it, then:

```bash
brew install python@3.13 node git
```

Use `python3` (Homebrew's) in the commands below. The system Python on older macOS versions is too old.

### Windows 10 / 11

Using PowerShell and [winget](https://learn.microsoft.com/windows/package-manager/winget/) (built in to current Windows):

```powershell
winget install -e --id Python.Python.3.13
winget install -e --id OpenJS.NodeJS.LTS
winget install -e --id Git.Git
```

Close and reopen PowerShell afterwards so the new tools are on `PATH`. If you install Python from python.org instead, tick **Add python.exe to PATH**.

## Setup

Clone and enter the project:

```bash
git clone https://github.com/abhishekshukla81/stock_index_app.git
cd stock_index_app
```

### 1. Python environment and dependencies

Fedora / macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks the activate script ("running scripts is disabled"), run this once for your user and retry:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Windows (Command Prompt): use `.venv\Scripts\activate.bat` instead.

### 2. Build the React UI

Same on every OS. The build output (`frontend/dist`) is not stored in git, so this step is required after every fresh clone.

```bash
cd frontend
npm ci
npm run build
cd ..
```

## Run the app

With the virtual environment active:

```bash
python app.py        # Windows: python app.py  (or py app.py)
```

Open **http://127.0.0.1:5000**.

1. Choose an index. The scan starts in the background.
2. A progress bar shows stocks scanned. Large indices (S&P 500, NIFTY 500) can take several minutes.
3. Review the breakouts: click a column header to sort, use the box to filter.
4. **Export Excel** downloads the result. The **Constituents** tab lists the index tickers (CSV export).

Results for an index are reused for one hour.

## Develop the UI (optional, hot reload)

Run Flask as above, then in a second terminal:

```bash
cd frontend
npm run dev
```

Open **http://127.0.0.1:5173**. Edits in `frontend/src/` show up immediately, and `/api` calls are proxied to Flask on port 5000. Port 5000 keeps serving the last built bundle until you run `npm run build` again.

## Tests

With the virtual environment active:

```bash
python -m pytest -q
```

Tests run offline.

## Troubleshooting

| Problem | Fix |
|---|---|
| "This site can't be reached" | Use `http://127.0.0.1:5000` and make sure `python app.py` is running. The server is local-only, so a browser on another machine cannot connect. For a remote host, forward the port: `ssh -L 5000:127.0.0.1:5000 user@host` |
| Page says "UI not built" | Run step 2 (`npm ci && npm run build` in `frontend/`) |
| `Address already in use` on 5000 | Another process uses the port. Stop it, or change the port in `app.py` |
| Vite refuses to start on 5173 | Port is taken (strict port is on). Stop the other process |
| `npm ci` or `vite` fails with an engine/version error | Upgrade Node.js to 20.19+ or 22.12+ |
| Scan returns no rows or "Scan failed" | Check your internet connection. Yahoo Finance may rate-limit; wait a few minutes and rerun |
| `python` not found (Windows) | Use `py`, or reopen PowerShell after installing Python |
| Corporate proxy / TLS errors | Set `HTTPS_PROXY` and `REQUESTS_CA_BUNDLE` for your environment. Do not disable certificate verification |

## Google Colab

Colab has no Node.js, so build `frontend/dist` on your machine first and upload the whole folder. Then:

```python
%cd stock_index_app
!pip install -q -r requirements.txt
%run colab_run.py
```

## API

| Method | Path | Description |
|---|---|---|
| GET | `/api/indices` | Supported index names |
| GET | `/api/constituents?index=<name>` | Tickers for an index (JSON) |
| GET | `/api/export?index=<name>` | Tickers as CSV |
| POST | `/api/scan?index=<name>` | Start (or reuse) a background scan |
| GET | `/api/scan/<job_id>` | Scan progress and results |
| GET | `/api/scan/<job_id>/export` | Results as Excel (.xlsx) |

## Disclaimer

Data comes from Yahoo Finance and index providers and may be delayed or incomplete. This is an analysis aid, not investment advice. The DAX 40 and ISEQ 20 lists are static snapshots; verify them before relying on them.
