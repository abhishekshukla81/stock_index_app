import io
import sys
from pathlib import Path
from unittest import mock

import pandas as pd
import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app as webapp  # noqa: E402
import stock_universe as su  # noqa: E402


class FakeResp:
    def __init__(self, content=b"", text="", json_data=None):
        self.content = content
        self.text = text
        self._json = json_data

    def json(self):
        return self._json

    def raise_for_status(self):
        pass


def _xlsx(tickers, column="Ticker"):
    buf = io.BytesIO()
    meta = pd.DataFrame([["Fund Name:", "SPY"]] * 4)
    body = pd.DataFrame({column: tickers})
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        meta.to_excel(w, index=False, header=False, startrow=0)
        body.to_excel(w, index=False, startrow=4)
    return buf.getvalue()


def test_sp500_filters_cash_usd_and_fixes_class_shares():
    # "CASH"/"USD" used to leak through due to operator precedence bug.
    data = _xlsx(["AAPL", "BRK.B", "CASH", "USD", "-", "Disclaimer text here", None])
    with mock.patch.object(su.requests, "get", return_value=FakeResp(content=data)):
        assert su.fetch_global_stocks("sp500") == ["AAPL", "BRK-B"]


def _qqq(rows):
    return FakeResp(content=b"{}", json_data={"holdings": rows})


def test_nasdaq_keeps_hyphenated_tickers_and_drops_non_equity():
    # Hyphenated class shares used to be dropped by isalpha().
    rows = [
        {"ticker": "AAPL", "securityTypeName": "Common Stock"},
        {"ticker": "BF.B", "securityTypeName": "Common Stock"},
        {"ticker": "ASML", "securityTypeName": "American Depository Receipt - NY"},
        {"ticker": "USD", "securityTypeName": "Currency"},
        {"ticker": "NQZ6", "securityTypeName": "Index Future"},
        {"ticker": None, "securityTypeName": "Synthetic Cash"},
    ]
    with mock.patch.object(su.requests, "get", return_value=_qqq(rows)):
        assert su.fetch_global_stocks("NDX") == ["AAPL", "BF-B", "ASML"]


def test_nifty_suffix_and_dedupe():
    csv_text = "Company,Symbol\nA,RELIANCE\nB,TCS\nC,TCS\n"
    with mock.patch.object(su.requests, "get", return_value=FakeResp(text=csv_text)):
        assert su.fetch_global_stocks("nifty 50") == ["RELIANCE.NS", "TCS.NS"]


def test_unknown_nifty_variant_is_rejected_not_defaulted():
    with pytest.raises(su.UnsupportedIndexError):
        su.fetch_global_stocks("NIFTY BANK")


def test_unsupported_vs_failure_are_distinct():
    with pytest.raises(su.UnsupportedIndexError):
        su.fetch_global_stocks("FTSE")
    with mock.patch.object(su.requests, "get", side_effect=requests.ConnectionError("x")):
        with pytest.raises(su.DataSourceError):
            su.fetch_global_stocks("S&P 500")


def test_changed_layout_raises_data_source_error():
    data = _xlsx(["AAPL"], column="Symbol")
    with mock.patch.object(su.requests, "get", return_value=FakeResp(content=data)):
        with pytest.raises(su.DataSourceError):
            su.fetch_global_stocks("S&P 500")


def test_static_lists_and_dhl_fix():
    dax = su.fetch_global_stocks("dax")
    assert len(dax) == 40 and "DHL.DE" in dax and "DPW.DE" not in dax
    assert len(su.fetch_global_stocks("ISEQ")) == 16


def test_formula_injection_tickers_dropped():
    rows = [
        {"ticker": "AAPL", "securityTypeName": "Common Stock"},
        {"ticker": "=cmd|' /C calc'!A0", "securityTypeName": "Common Stock"},
    ]
    with mock.patch.object(su.requests, "get", return_value=_qqq(rows)):
        assert su.fetch_global_stocks("NASDAQ 100") == ["AAPL"]


@pytest.fixture
def client():
    webapp._cache.clear()
    webapp.app.testing = True
    return webapp.app.test_client()


def test_api_flow_and_csv_export(client):
    assert "DAX 40" in client.get("/api/indices").get_json()["indices"]
    r = client.get("/api/constituents?index=DAX")
    assert r.status_code == 200 and r.get_json()["count"] == 40
    r = client.get("/api/export?index=DAX")
    assert r.mimetype == "text/csv"
    assert r.data.decode().splitlines()[:2] == ["index,ticker", "DAX 40,ADS.DE"]
    assert "attachment" in r.headers["Content-Disposition"]
    assert "Content-Security-Policy" in r.headers


def test_api_errors_are_generic(client):
    r = client.get("/api/constituents?index=nope")
    assert r.status_code == 400 and r.get_json() == {"error": "Unsupported index"}
    with mock.patch.object(su.requests, "get", side_effect=requests.ConnectionError("secret")):
        r = client.get("/api/constituents?index=S%26P%20500")
    assert r.status_code == 502 and "secret" not in r.get_data(as_text=True)
