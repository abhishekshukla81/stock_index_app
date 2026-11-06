"""Breakout scanner: price > 30/50/200 DMA and a rising CAR since the 52-week closing high.

CAR is the expanding mean of closing prices starting at the 52-week closing high.
It is "Positive" when its last 10 values never decrease.
"""

import logging
import warnings
from datetime import datetime

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)
logging.getLogger("yfinance").setLevel(logging.CRITICAL)

BATCH_SIZE = 25
MIN_HISTORY = 200  # trading days needed for the 200 DMA
CAR_WINDOW = 10

COLUMNS = [
    "Date", "Ticker", "Stock", "CMP", "52W High", "52W High Date", "30 DMA", "50 DMA", "200 DMA",
    "200 DMA Dist %", "CAR Status", "Action",
]


def evaluate(ticker, close, today=None):
    """Return a result row if ``ticker`` is a positive breakout, else ``None``."""
    close = close.dropna()
    if len(close) < MIN_HISTORY:
        return None

    dma_30 = close.rolling(30).mean().iloc[-1]
    dma_50 = close.rolling(50).mean().iloc[-1]
    dma_200 = close.rolling(200).mean().iloc[-1]
    cmp = close.iloc[-1]

    # 52-week high on closing prices, then CAR from that date onwards.
    high_date = close.tail(252).idxmax()
    car_data = close.loc[high_date:]
    if len(car_data) < CAR_WINDOW:
        return None
    car_positive = car_data.expanding().mean().tail(CAR_WINDOW).is_monotonic_increasing

    if not (cmp > dma_30 and cmp > dma_50 and cmp > dma_200 and car_positive):
        return None

    return {
        "Date": today or datetime.now().strftime("%d-%m-%Y"),
        "Ticker": ticker,
        "Stock": ticker.split(".")[0],
        "CMP": round(float(cmp), 2),
        "52W High": round(float(close.loc[high_date]), 2),
        "52W High Date": high_date.strftime("%d-%m-%Y"),
        "30 DMA": round(float(dma_30), 2),
        "50 DMA": round(float(dma_50), 2),
        "200 DMA": round(float(dma_200), 2),
        "200 DMA Dist %": round(float((cmp - dma_200) / dma_200 * 100), 2),
        "CAR Status": "Positive",
        "Action": "Positive Breakout",
    }


def _closes(batch):
    """Download 2y daily closes for a batch; returns {ticker: Series}."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        data = yf.download(
            batch, period="2y", interval="1d", progress=False,
            group_by="ticker", threads=True, timeout=20,
        )
    if data is None or data.empty:
        return {}
    out = {}
    for t in batch:
        try:
            col = data[t]["Close"] if isinstance(data.columns, pd.MultiIndex) else data["Close"]
            out[t] = col.squeeze()
        except KeyError:
            continue
    return out


def scan(tickers, progress=None, today=None):
    """Scan ``tickers``; call ``progress(done, total)`` after each batch.

    Returns a DataFrame of positive breakouts sorted by distance from the 200 DMA
    (ascending, i.e. the least extended first).
    """
    rows = []
    total = len(tickers)
    for i in range(0, total, BATCH_SIZE):
        batch = tickers[i:i + BATCH_SIZE]
        try:
            closes = _closes(batch)
        except Exception:
            logger.warning("Batch download failed", exc_info=True)
            closes = {}
        for t, series in closes.items():
            try:
                row = evaluate(t, series, today)
            except Exception:
                logger.warning("Evaluation failed for %s", t, exc_info=True)
                continue
            if row:
                rows.append(row)
        if progress:
            progress(min(i + BATCH_SIZE, total), total)

    df = pd.DataFrame(rows, columns=COLUMNS)
    if not df.empty:
        df = df.sort_values("200 DMA Dist %").reset_index(drop=True)
    return df
