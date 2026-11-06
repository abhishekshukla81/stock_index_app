import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scanner  # noqa: E402


def _series(values):
    idx = pd.bdate_range("2023-01-02", periods=len(values))
    return pd.Series(values, index=idx, dtype=float)


def _pullback_recovery():
    # Peak at 200, dip to 170, recover to 195: above all DMAs, CAR turns up.
    return _series(np.concatenate([
        np.linspace(100, 200, 260), np.linspace(200, 170, 15), np.linspace(170, 195, 25),
    ]))


def test_uptrend_is_positive_breakout():
    row = scanner.evaluate("AAA.NS", _pullback_recovery(), today="01-01-2024")
    assert row["Stock"] == "AAA"
    assert row["CAR Status"] == "Positive"
    assert row["CMP"] == 195.0
    assert row["52W High"] == 200.0
    assert row["52W High Date"] == _pullback_recovery().idxmax().strftime("%d-%m-%Y")


def test_downtrend_is_rejected():
    assert scanner.evaluate("BBB", _series(np.linspace(200, 100, 300))) is None


def test_short_history_is_rejected():
    assert scanner.evaluate("CCC", _series(np.linspace(100, 200, 150))) is None


def test_falling_car_after_high_is_rejected():
    # Rise, peak, then drop but still above the 200 DMA: CAR is falling.
    vals = np.concatenate([np.linspace(50, 300, 280), np.linspace(300, 270, 20)])
    assert scanner.evaluate("DDD", _series(vals)) is None


def test_scan_sorts_and_reports_progress():
    up = _pullback_recovery()
    up2 = up * 2 + 50  # smaller % distance from its 200 DMA
    calls = []
    with __import__("unittest.mock").mock.patch.object(
        scanner, "_closes", return_value={"A": up, "B": up2}
    ):
        df = scanner.scan(["A", "B"], progress=lambda d, t: calls.append((d, t)))
    assert list(df["Ticker"]) == ["B", "A"]
    assert calls == [(2, 2)]
