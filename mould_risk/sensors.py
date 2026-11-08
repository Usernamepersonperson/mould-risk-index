"""Cheap temperature / humidity sensor side: payload format, BLE parsing, error model, data gaps.

Open 7-byte uplink format used by this project (identical for LoRaWAN FPort 1 and the BLE
manufacturer-specific advertising data; the JavaScript decoder in codec/ decodes the same bytes):

    byte 0      version (high nibble, = 1) | flags (low nibble: bit0 low battery, bit1 sensor fault)
    bytes 1-2   temperature, int16 big endian, 0.01 C   (0x8000 = invalid)
    bytes 3-4   relative humidity, uint16 big endian, 0.01 %   (0xFFFF = invalid)
    byte 5      battery, uint8, 2.00 V + 0.01 V * value
    byte 6      frame counter, uint8 (wraps at 256), used to detect lost packets

Placement guidance (see README): put the sensor (a) on the room-side of the coldest spot, typically the
upper corner of an external wall or a window reveal, 5-10 cm from the surface and 30 cm from corners
of ceiling, never behind a curtain or furniture; (b) one reference sensor in the room centre at about
1.5 m height away from radiators and windows. The corner sensor sees the surface-side air directly; the
reference sensor needs an assumed fRsi to estimate the wall surface RH.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

import numpy as np
import pandas as pd

VERSION = 1
FLAG_LOW_BATT = 0x1
FLAG_FAULT = 0x2
T_INVALID = -32768
RH_INVALID = 0xFFFF


class PayloadError(ValueError):
    pass


def encode_payload(t_c: float | None, rh_pct: float | None, batt_v: float, counter: int, flags: int = 0) -> bytes:
    if not 0 <= flags <= 0xF:
        raise PayloadError("flags must fit in 4 bits")
    t_raw = T_INVALID if t_c is None else int(round(t_c * 100))
    if t_c is not None and not -32767 <= t_raw <= 32767:
        raise PayloadError("temperature out of range")
    rh_raw = RH_INVALID if rh_pct is None else int(round(rh_pct * 100))
    if rh_pct is not None and not 0 <= rh_raw <= 10000:
        raise PayloadError("humidity out of range 0..100 %")
    b_raw = int(round((batt_v - 2.0) * 100))
    if not 0 <= b_raw <= 255:
        raise PayloadError("battery voltage out of range 2.00..4.55 V")
    return struct.pack(">BhHBB", (VERSION << 4) | flags, t_raw, rh_raw, b_raw, counter & 0xFF)


def decode_payload(data: bytes) -> dict:
    if len(data) != 7:
        raise PayloadError(f"expected 7 bytes, got {len(data)}")
    b0, t_raw, rh_raw, b_raw, counter = struct.unpack(">BhHBB", bytes(data))
    if b0 >> 4 != VERSION:
        raise PayloadError(f"unsupported payload version {b0 >> 4}")
    t = None if t_raw == T_INVALID else t_raw / 100.0
    if rh_raw == RH_INVALID:
        rh = None
    elif rh_raw > 10000:
        raise PayloadError("humidity above 100 %")
    else:
        rh = rh_raw / 100.0
    return {
        "temperature_c": t,
        "humidity_pct": rh,
        "battery_v": 2.0 + b_raw / 100.0,
        "counter": counter,
        "low_battery": bool(b0 & FLAG_LOW_BATT),
        "fault": bool(b0 & FLAG_FAULT),
    }


def parse_ble_advertisement(adv: bytes, company_id: int = 0xFFFF) -> dict:
    """Find the manufacturer-specific AD structure (type 0xFF) with our company id and decode it."""
    i = 0
    while i < len(adv):
        ln = adv[i]
        if ln == 0:
            break
        if i + 1 + ln > len(adv):
            raise PayloadError("truncated AD structure")
        ad_type = adv[i + 1]
        body = adv[i + 2 : i + 1 + ln]
        if ad_type == 0xFF and len(body) >= 2 and int.from_bytes(body[:2], "little") == company_id:
            return decode_payload(body[2:])
        i += 1 + ln
    raise PayloadError("no matching manufacturer data in advertisement")


def build_ble_advertisement(payload: bytes, company_id: int = 0xFFFF) -> bytes:
    flags = bytes([2, 0x01, 0x06])
    body = company_id.to_bytes(2, "little") + payload
    return flags + bytes([len(body) + 1, 0xFF]) + body


@dataclass
class SensorModel:
    """Error model of a low-cost capacitive T/RH sensor (typical datasheet class: +-0.3 K, +-3 % RH)."""

    t_sigma: float = 0.15
    rh_sigma: float = 1.5
    rh_bias_sigma: float = 1.5  # fixed per-unit offset
    loss_prob: float = 0.05  # independent packet loss
    outage_prob_per_day: float = 0.01  # start of a multi-hour outage (battery, range)
    outage_hours: tuple[int, int] = (6, 36)

    def observe(self, t_true, rh_true, rng: np.random.Generator):
        t = np.asarray(t_true, dtype=float)
        rh = np.asarray(rh_true, dtype=float)
        bias = rng.normal(0, self.rh_bias_sigma)
        t_m = t + rng.normal(0, self.t_sigma, t.shape)
        rh_m = np.clip(rh + bias + rng.normal(0, self.rh_sigma, rh.shape), 1.0, 100.0)
        return t_m, rh_m

    def gap_mask(self, n_hours: int, rng: np.random.Generator) -> np.ndarray:
        """Boolean mask, True where the reading is missing."""
        lost = rng.random(n_hours) < self.loss_prob
        p_start = self.outage_prob_per_day / 24.0
        i = 0
        while i < n_hours:
            if rng.random() < p_start:
                ln = int(rng.integers(self.outage_hours[0], self.outage_hours[1] + 1))
                lost[i : i + ln] = True
                i += ln
            i += 1
        return lost


def apply_gaps(series: pd.Series, mask: np.ndarray) -> pd.Series:
    s = series.copy()
    s[mask] = np.nan
    return s


def fill_short_gaps(series: pd.Series, limit_hours: int = 3) -> pd.Series:
    """Linear-interpolate gaps of at most limit_hours; longer gaps stay NaN (never invent data)."""
    filled = series.interpolate(limit=limit_hours, limit_area="inside")
    # interpolate(limit=) also fills the first `limit` hours of a longer gap; mask those back
    gap = series.isna()
    run_id = (gap != gap.shift()).cumsum()
    run_len = gap.groupby(run_id).transform("sum")
    filled[gap & (run_len > limit_hours)] = np.nan
    return filled


def lost_packets(counters: list[int]) -> int:
    """Number of missing frames given the received frame counters (uint8 wrap-around aware)."""
    lost = 0
    for a, b in zip(counters, counters[1:], strict=False):
        lost += ((b - a) & 0xFF) - 1
    return lost


def coverage(series: pd.Series) -> float:
    """Share of non-missing samples in %."""
    return 100.0 * float(series.notna().mean()) if len(series) else 0.0
