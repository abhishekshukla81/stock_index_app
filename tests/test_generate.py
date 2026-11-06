import json
import sys
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pages_app"))

import generate  # noqa: E402
import scanner  # noqa: E402
from stock_universe import DataSourceError  # noqa: E402


def _good():
    idx = pd.bdate_range("2023-01-02", periods=300)
    vals = np.concatenate([np.linspace(100, 200, 260), np.linspace(200, 170, 15), np.linspace(170, 195, 25)])
    return pd.Series(vals, index=idx)


def test_slug():
    assert generate.slug("S&P 500") == "s-p-500"
    assert generate.slug("NIFTY MIDCAP 150") == "nifty-midcap-150"


def test_scan_index_result_shape():
    with mock.patch.object(generate, "fetch_global_stocks", return_value=["A", "B"]), \
         mock.patch.object(scanner, "_closes", return_value={"A": _good(), "B": _good()}):
        r = generate.scan_index("DAX 40", today="01-01-2024")
    assert (r["index"], r["total"], r["count"], r["no_data"]) == ("DAX 40", 2, 2, 0)
    assert r["rows"][0]["52W High"] == 200.0


def test_main_writes_json_xlsx_and_manifest(tmp_path):
    fake = {"index": "DAX 40", "generated_at": "t", "total": 2, "no_data": 0, "count": 1,
            "rows": [{"Ticker": "A", "CMP": 1.0}]}
    with mock.patch.object(generate, "scan_index", return_value=fake):
        assert generate.main(["--out", str(tmp_path), "--only", "DAX 40"]) == 0
    assert json.loads((tmp_path / "dax-40.json").read_text())["count"] == 1
    assert list(pd.read_excel(tmp_path / "dax-40.xlsx")["Ticker"]) == ["A"]
    m = json.loads((tmp_path / "manifest.json").read_text())
    assert m["indices"][0]["xlsx"] == "dax-40.xlsx"


def test_low_coverage_is_rejected():
    with mock.patch.object(generate, "fetch_global_stocks", return_value=["A", "B", "C", "D", "E"]), \
         mock.patch.object(scanner, "_closes", return_value={"A": _good()}):
        with pytest.raises(DataSourceError):
            generate.scan_index("DAX 40")


def test_main_keeps_previous_file_when_index_fails(tmp_path):
    old = {"index": "DAX 40", "generated_at": "2020-01-01T00:00:00+00:00", "total": 40,
           "no_data": 0, "count": 1, "rows": [{"Ticker": "X"}]}
    (tmp_path / "dax-40.json").write_text(json.dumps(old))
    with mock.patch.object(generate, "scan_index", side_effect=DataSourceError("boom")):
        assert generate.main(["--out", str(tmp_path), "--only", "DAX 40"]) == 0
    kept = json.loads((tmp_path / "dax-40.json").read_text())
    assert kept["stale"] is True and kept["rows"] == [{"Ticker": "X"}]
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["indices"][0]["stale"] is True


def test_main_fails_when_nothing_produced(tmp_path):
    with mock.patch.object(generate, "scan_index", side_effect=DataSourceError("boom")):
        assert generate.main(["--out", str(tmp_path), "--only", "DAX 40"]) == 1
