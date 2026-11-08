import numpy as np
import pandas as pd
import pytest

from mould_risk import weather
from mould_risk.alerts import count_alerts, episodes, evaluate_sensing, merge_runs, sensor_view
from mould_risk.report import render_weekly
from mould_risk.sensors import SensorModel
from mould_risk.sim import (
    ALTBAU,
    BAD,
    BEHAVIOURS,
    BUILDINGS,
    GOOD,
    RENOVATED,
    TYPICAL,
    AdvicePolicy,
    airing_minutes_per_day,
    simulate,
    summarize,
)


@pytest.fixture(scope="module")
def w():
    return weather.load_city("zurich").loc["2025-12-01":"2026-01-20"]


@pytest.fixture(scope="module")
def runs(w):
    return {(b.key, h.key): simulate(w, b, h) for b in BUILDINGS.values() for h in BEHAVIOURS.values()}


def test_weather_files_complete():
    for city in weather.CITIES:
        df = weather.load_city(city)
        assert len(df) == 4032
        assert df["temp_c"].between(-35, 35).all() and df["rh_pct"].between(0, 100).all()
        assert str(df.index.tz) == "Europe/Zurich"


def test_weather_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        weather.load_city("zurich", tmp_path)


def test_davos_colder_than_lugano():
    assert weather.load_city("davos")["temp_c"].mean() < weather.load_city("lugano")["temp_c"].mean() - 3


def test_airing_minutes():
    assert airing_minutes_per_day(BAD) == 0
    assert airing_minutes_per_day(TYPICAL) == 10
    assert 20 < airing_minutes_per_day(GOOD) < 40


def test_simulation_is_deterministic(w):
    a = simulate(w, RENOVATED, TYPICAL, seed=3)
    b = simulate(w, RENOVATED, TYPICAL, seed=3)
    pd.testing.assert_frame_equal(a, b)


def test_physical_ordering_of_temperatures(runs):
    for df in runs.values():
        assert (df["t_surf"] < df["t_in"]).mean() > 0.99
        assert df["t_in"].between(10, 28).all()
        assert df["rh_in"].between(5, 98.5).all()


def test_good_airing_is_drier_than_bad_habits(runs):
    for b in ("altbau", "renovated"):
        assert runs[(b, "good")]["rh_in"].mean() < runs[(b, "bad")]["rh_in"].mean() - 5


def test_tight_envelope_needs_airing_more_than_old_building(runs):
    assert runs[("renovated", "bad")]["rh_in"].mean() > runs[("altbau", "bad")]["rh_in"].mean()


def test_renovated_uses_less_heating_energy(runs):
    assert summarize(runs[("renovated", "typical")])["heating_kwh"] < summarize(runs[("altbau", "typical")])["heating_kwh"]


def test_mould_index_ordering(runs):
    for b in ("altbau", "renovated"):
        assert runs[(b, "bad")]["mould_idx"].max() >= runs[(b, "typical")]["mould_idx"].max() >= runs[(b, "good")]["mould_idx"].max()


def test_airing_lowers_surface_rh(w):
    base = simulate(w, ALTBAU, BAD)
    aired = simulate(w, ALTBAU, BAD, extra_air_min_per_day=20)
    assert aired["rh_surf"].mean() < base["rh_surf"].mean()


def test_higher_setpoint_raises_surface_temperature(w):
    base = simulate(w, ALTBAU, BAD)
    warm = simulate(w, ALTBAU, BAD, setpoint_offset=2.0)
    assert warm["t_surf"].mean() > base["t_surf"].mean() + 0.5


def test_wardrobe_penalty_lowers_corner_temperature(w):
    from mould_risk.sim import with_behaviour

    a = simulate(w, ALTBAU, with_behaviour(BAD, wardrobe_penalty=0.0))
    b = simulate(w, ALTBAU, BAD)
    assert b["t_surf"].mean() < a["t_surf"].mean()


def test_advice_policy_reduces_risk(w):
    base = simulate(w, RENOVATED, BAD)
    pol = AdvicePolicy(mode="corner", compliance=0.9)
    looped = simulate(w, RENOVATED, BAD, policy=pol)
    assert pol.n_advice > 0
    assert looped["rh_surf"].mean() < base["rh_surf"].mean()


def test_episodes_and_merge():
    f = [0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1]
    assert episodes(f, 3, merge_gap=0) == [(1, 3), (6, 8), (15, 17)]
    assert episodes(f, 3, merge_gap=2) == [(1, 8), (15, 17)]
    assert merge_runs([], 3) == []
    assert episodes([np.nan, 1, 1, 1], 3) == [(1, 3)]


def test_count_alerts_on_synthetic_series():
    idx = pd.date_range("2026-01-01", periods=48, freq="h")
    rh = pd.Series(np.r_[np.full(10, 60.0), np.full(5, 82.0), np.full(33, 60.0)], idx)
    c = count_alerts(rh, np.zeros(48))
    assert c == {"watch": 1, "warn": 1, "critical": 0}
    assert count_alerts(rh, np.r_[np.zeros(20), np.full(28, 1.5)])["critical"] == 1


def test_perfect_sensing_gives_perfect_scores(runs):
    df = runs[("altbau", "bad")]
    view = pd.DataFrame({"rh_surf_est": df["rh_surf"], "coverage_pct": 100.0})
    e = evaluate_sensing(df, view)
    assert e["hour_precision"] == 1.0 and e["hour_recall"] == 1.0
    assert e["false_alarm_episodes"] == 0 and e["missed_episodes"] == 0


def test_corner_sensor_estimates_closer_than_generic_room_sensor(runs):
    df = runs[("altbau", "bad")]
    err = {s: evaluate_sensing(df, sensor_view(df, ALTBAU.frsi_corner, s, seed=1))["mean_abs_err_rh_surf"]
           for s in ("room_generic", "corner")}
    assert err["corner"] < err["room_generic"]


def test_sensor_view_rejects_unknown_setup(runs):
    with pytest.raises(ValueError):
        sensor_view(runs[("altbau", "bad")], 0.6, "attic")


def test_data_gaps_reduce_coverage_but_never_invent_data(runs):
    df = runs[("renovated", "typical")]
    v = sensor_view(df, RENOVATED.frsi_corner, "corner", seed=5, model=SensorModel(loss_prob=0.1))
    assert 80 < v["coverage_pct"].iloc[0] < 100
    assert v["m_est"].notna().all()


@pytest.mark.parametrize("lang", ["de", "fr", "it", "en"])
def test_weekly_report_renders_neutral_and_private(runs, lang):
    df = runs[("renovated", "typical")]
    v = sensor_view(df, RENOVATED.frsi_corner, "corner", seed=0)
    wk = slice("2026-01-05", "2026-01-11")
    txt = render_weekly("Flat 3 (simulated)", v.loc[wk], df["t_out"].loc[wk], df["rh_out"].loc[wk], 0.74, lang)
    assert "{{" not in txt and "{" not in txt
    assert "Flat 3" in txt and "2026-01-05" in txt
    low = txt.lower()
    assert ("cloud" in low) and ("fRsi" in txt)
