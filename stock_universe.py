"""Constituent loader for global stock indices.

Remote sources (ETF issuer / index provider files):
  * S&P 500   - State Street SPDR SPY daily holdings (xlsx)
  * NASDAQ 100 - Invesco QQQ holdings (csv)
  * NIFTY *   - niftyindices.com constituent csv files

Static snapshots (NOT live, verify before relying on them):
  * DAX 40, ISEQ 20

Tickers are returned in Yahoo Finance format.
"""

import io
import logging
import re

import pandas as pd
import requests

logger = logging.getLogger(__name__)

# Descriptive UA instead of spoofing a browser.
HEADERS = {"User-Agent": "stock-universe-loader/1.0 (+python-requests)"}
TIMEOUT = 15
MAX_BYTES = 10 * 1024 * 1024  # refuse downloads larger than 10 MB

SPY_URL = (
    "https://www.ssga.com/us/en/intermediary/etfs/library-content/products/"
    "fund-data/etfs/us/holdings-daily-us-en-spy.xlsx"
)
# The old holdings-0.csv download now returns an HTML page; use the JSON API.
QQQ_URL = (
    "https://dng-api.invesco.com/cache/v1/accounts/en_US/shareclasses/QQQ/"
    "holdings/fund?idType=ticker&interval=monthly&productType=ETF"
)
NIFTY_BASE = "https://niftyindices.com/IndexConstituent/"
NIFTY_FILES = {
    "NIFTY 50": "ind_nifty50list.csv",
    "NIFTY 100": "ind_nifty100list.csv",
    "NIFTY 200": "ind_nifty200list.csv",
    "NIFTY 500": "ind_nifty500list.csv",
    "NIFTY MIDCAP 150": "ind_niftymidcap150list.csv",
}

# Static snapshots. Index membership changes (DAX quarterly) - verify regularly.
DAX_40 = [
    "ADS.DE", "AIR.DE", "ALV.DE", "BAS.DE", "BAYN.DE", "BEI.DE", "BMW.DE",
    "BNR.DE", "CBK.DE", "CON.DE", "1COV.DE", "DTG.DE", "DB1.DE", "DBK.DE",
    "LHA.DE", "DHL.DE",  # Deutsche Post renamed DHL Group (was DPW.DE)
    "DTE.DE", "EOAN.DE", "FRE.DE", "HNR1.DE", "HEI.DE", "HEN3.DE", "IFX.DE",
    "MBG.DE", "MRK.DE", "MTX.DE", "MUV2.DE", "P911.DE", "PAH3.DE", "QIA.DE",
    "RHM.DE", "RWE.DE", "SAP.DE", "SRT3.DE", "SIE.DE", "ENR.DE", "SHL.DE",
    "SY1.DE", "VOW3.DE", "ZAL.DE",
]
ISEQ_20 = [
    "AIBG.IR", "BIRG.IR", "KRZ.IR", "KRX.IR", "RY4C.IR", "GL9.IR", "C5H.IR",
    "GRP.IR", "IR5B.IR", "FBD.IR", "DHG.IR", "OIZ.IR", "KMR.IR", "GVP.IR",
    "MLC.IR", "UN0.IR",
]

# Canonical index name -> accepted aliases (compared upper-case, whitespace-normalised)
INDEX_ALIASES = {
    "S&P 500": ["S&P 500", "SP500", "S&P500"],
    "NASDAQ 100": ["NASDAQ 100", "NASDAQ", "NDX"],
    "DAX 40": ["DAX 40", "DAX", "DAX40"],
    "ISEQ 20": ["ISEQ 20", "ISEQ", "ISEQ20"],
    **{name: [name] for name in NIFTY_FILES},
}

_ALIAS_LOOKUP = {
    alias: canon for canon, aliases in INDEX_ALIASES.items() for alias in aliases
}

_US_TICKER = re.compile(r"^[A-Z]{1,5}(-[A-Z])?$")
# Safe output ticker: starts alphanumeric (blocks CSV formula injection).
_SAFE_TICKER = re.compile(r"^[A-Z0-9][A-Z0-9&.\-]{0,19}$")
_US_EXCLUDED = {"CASH", "USD"}


class UnsupportedIndexError(ValueError):
    """The requested index name is not supported."""


class DataSourceError(RuntimeError):
    """A remote source failed or returned data in an unexpected layout."""


def supported_indices():
    """Return the canonical names of all supported indices."""
    return list(INDEX_ALIASES)


def resolve_index(index_name):
    """Map user input to a canonical index name or raise UnsupportedIndexError."""
    key = " ".join(str(index_name).upper().split())
    try:
        return _ALIAS_LOOKUP[key]
    except KeyError:
        raise UnsupportedIndexError(f"Unsupported index: {index_name!r}") from None


def _download(url):
    res = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    res.raise_for_status()
    if len(res.content) > MAX_BYTES:
        raise DataSourceError("Response too large")
    return res


def _us_tickers(symbols):
    out = []
    for sym in symbols.dropna().astype(str).str.strip().str.upper():
        sym = sym.replace(".", "-")
        if sym not in _US_EXCLUDED and _US_TICKER.match(sym):
            out.append(sym)
    return out


def _sp500():
    # SSGA sheet carries metadata in the first 4 rows; header is on row 5.
    df = pd.read_excel(
        io.BytesIO(_download(SPY_URL).content), skiprows=4, engine="openpyxl"
    )
    return _us_tickers(df["Ticker"])


def _nasdaq100():
    holdings = _download(QQQ_URL).json()["holdings"]
    # Keep equities/ADRs only; drops futures, currency and cash rows.
    symbols = pd.Series(
        [
            h.get("ticker")
            for h in holdings
            if (h.get("securityTypeName") or "").startswith(
                ("Common Stock", "American Depository Receipt")
            )
        ],
        dtype="object",
    )
    return _us_tickers(symbols)


def _nifty(name):
    df = pd.read_csv(io.StringIO(_download(NIFTY_BASE + NIFTY_FILES[name]).text))
    return [f"{str(s).strip().upper()}.NS" for s in df["Symbol"].dropna()]


def _fetch(canonical):
    if canonical == "S&P 500":
        return _sp500()
    if canonical == "NASDAQ 100":
        return _nasdaq100()
    if canonical == "DAX 40":
        return list(DAX_40)
    if canonical == "ISEQ 20":
        return list(ISEQ_20)
    return _nifty(canonical)


def fetch_global_stocks(index_name="S&P 500"):
    """Return de-duplicated Yahoo-format tickers for ``index_name``.

    Raises:
        UnsupportedIndexError: unknown index name.
        DataSourceError: download or parse failure (details are logged).
    """
    canonical = resolve_index(index_name)
    logger.info("Loading constituents for %s", canonical)
    try:
        raw = _fetch(canonical)
    except (requests.RequestException, KeyError, ValueError, ImportError) as exc:
        logger.error("Failed to load %s: %s", canonical, type(exc).__name__,
                     exc_info=True)
        raise DataSourceError(f"Could not load constituents for {canonical}") from exc

    tickers = list(dict.fromkeys(t for t in raw if _SAFE_TICKER.match(t)))
    if not tickers:
        raise DataSourceError(f"No constituents found for {canonical}")
    logger.info("Loaded %d constituents for %s", len(tickers), canonical)
    return tickers
