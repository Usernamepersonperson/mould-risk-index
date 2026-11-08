import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from mould_risk.sensors import (
    PayloadError,
    SensorModel,
    apply_gaps,
    build_ble_advertisement,
    coverage,
    decode_payload,
    encode_payload,
    fill_short_gaps,
    lost_packets,
    parse_ble_advertisement,
)

ROOT = Path(__file__).resolve().parent.parent


def test_payload_roundtrip():
    raw = encode_payload(19.37, 63.42, 3.05, 17)
    d = decode_payload(raw)
    assert d["temperature_c"] == pytest.approx(19.37)
    assert d["humidity_pct"] == pytest.approx(63.42)
    assert d["battery_v"] == pytest.approx(3.05)
    assert d["counter"] == 17 and not d["low_battery"] and not d["fault"]
    assert len(raw) == 7


def test_payload_negative_temperature():
    assert decode_payload(encode_payload(-12.5, 80.0, 3.0, 0))["temperature_c"] == pytest.approx(-12.5)


def test_payload_invalid_markers():
    d = decode_payload(encode_payload(None, None, 3.0, 1))
    assert d["temperature_c"] is None and d["humidity_pct"] is None


def test_payload_flags():
    d = decode_payload(encode_payload(20.0, 50.0, 2.4, 1, flags=0x3))
    assert d["low_battery"] and d["fault"]


@pytest.mark.parametrize("n", [0, 3, 6, 8, 20])
def test_payload_wrong_length(n):
    with pytest.raises(PayloadError):
        decode_payload(bytes(n))


def test_payload_wrong_version():
    raw = bytearray(encode_payload(20.0, 50.0, 3.0, 0))
    raw[0] = 0x20
    with pytest.raises(PayloadError):
        decode_payload(bytes(raw))


def test_payload_humidity_above_100_rejected_on_decode():
    raw = bytearray(encode_payload(20.0, 50.0, 3.0, 0))
    raw[3:5] = (12000).to_bytes(2, "big")
    with pytest.raises(PayloadError):
        decode_payload(bytes(raw))


def test_encode_rejects_out_of_range():
    with pytest.raises(PayloadError):
        encode_payload(20.0, 120.0, 3.0, 0)
    with pytest.raises(PayloadError):
        encode_payload(400.0, 50.0, 3.0, 0)
    with pytest.raises(PayloadError):
        encode_payload(20.0, 50.0, 5.5, 0)


def test_lost_packets_with_wraparound():
    assert lost_packets([1, 2, 3]) == 0
    assert lost_packets([1, 4, 5]) == 2
    assert lost_packets([254, 255, 0, 1]) == 0
    assert lost_packets([250, 2]) == 7


def test_ble_roundtrip_and_extra_structures():
    raw = encode_payload(18.2, 71.0, 2.9, 200)
    adv = build_ble_advertisement(raw)
    assert parse_ble_advertisement(adv)["humidity_pct"] == pytest.approx(71.0)


def test_ble_wrong_company_and_truncation():
    adv = build_ble_advertisement(encode_payload(18.2, 71.0, 2.9, 1), company_id=0x1234)
    with pytest.raises(PayloadError):
        parse_ble_advertisement(adv)
    with pytest.raises(PayloadError):
        parse_ble_advertisement(adv[:-3])


def test_fill_short_gaps_only_fills_short_runs():
    idx = pd.date_range("2026-01-01", periods=12, freq="h")
    s = pd.Series(np.arange(12, dtype=float), idx)
    s.iloc[2:4] = np.nan  # 2 h gap
    s.iloc[6:11] = np.nan  # 5 h gap
    f = fill_short_gaps(s, limit_hours=3)
    assert f.iloc[2:4].notna().all()
    assert f.iloc[6:11].isna().all()


def test_apply_gaps_and_coverage():
    s = pd.Series(np.ones(10))
    g = apply_gaps(s, np.array([True] * 3 + [False] * 7))
    assert coverage(g) == pytest.approx(70.0)
    assert coverage(pd.Series([], dtype=float)) == 0.0


def test_gap_mask_rate_is_close_to_configured_loss():
    m = SensorModel(loss_prob=0.05, outage_prob_per_day=0.0)
    mask = m.gap_mask(20000, np.random.default_rng(1))
    assert mask.mean() == pytest.approx(0.05, abs=0.01)


def test_sensor_noise_is_bounded_and_clipped():
    m = SensorModel()
    t, rh = m.observe(np.full(1000, 20.0), np.full(1000, 99.5), np.random.default_rng(2))
    assert abs(t.mean() - 20.0) < 0.05
    assert rh.max() <= 100.0


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
@pytest.mark.parametrize(
    "args",
    [(19.37, 63.42, 3.05, 17, 0), (-12.5, 80.0, 2.4, 255, 1), (None, None, 3.3, 0, 2), (0.0, 100.0, 4.5, 9, 0)],
)
def test_js_decoder_matches_python(args):
    raw = encode_payload(*args)
    out = subprocess.run(["node", str(ROOT / "codec" / "decode_hex.js"), raw.hex()], capture_output=True, text=True, check=True)
    js = json.loads(out.stdout)
    py = decode_payload(raw)
    assert js["errors"] == []
    for k in ("temperature_c", "humidity_pct", "battery_v", "counter", "low_battery", "fault"):
        assert js["data"][k] == pytest.approx(py[k])


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_js_decoder_rejects_bad_input():
    out = subprocess.run(["node", str(ROOT / "codec" / "decode_hex.js"), "1000"], capture_output=True, text=True, check=True)
    assert json.loads(out.stdout)["errors"]
