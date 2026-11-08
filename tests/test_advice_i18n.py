import string

import pytest

from mould_risk.advice import Reading, advise, required_frsi, surface_rh_of
from mould_risk.cli import main
from mould_risk.i18n import ADVICE, LANGS, REPORT, SEVERITY, tr


def _fields(text):
    return {f for _, f, _, _ in string.Formatter().parse(text) if f}


@pytest.mark.parametrize("table", [ADVICE, REPORT, SEVERITY])
def test_every_key_has_all_four_languages(table):
    for key, entry in table.items():
        assert set(entry) == set(LANGS), key


@pytest.mark.parametrize("table", [ADVICE, REPORT])
def test_placeholders_identical_across_languages(table):
    for key, entry in table.items():
        sets = {lang: _fields(entry[lang]) for lang in LANGS}
        assert len({frozenset(v) for v in sets.values()}) == 1, key


def test_no_german_eszett_in_swiss_texts():
    assert all("ß" not in e["de"] for e in list(ADVICE.values()) + list(REPORT.values()))


def test_unknown_language_falls_back_to_english():
    assert tr(ADVICE, "ok", "rm") == ADVICE["ok"]["en"]


def _moist(**kw):
    base = dict(t_in=19.0, rh_in=68.0, t_out=0.0, rh_out=85.0, frsi=0.66)
    base.update(kw)
    return Reading(**base)


def test_ok_when_dry():
    a = advise(Reading(21.0, 40.0, 0.0, 80.0, 0.8))
    assert [x.code for x in a] == ["ok"]


def test_moist_room_gets_airing_and_heating_advice():
    codes = [x.code for x in advise(_moist())]
    assert "air_now" in codes
    assert "heat_up" in codes or "heat_not_enough" in codes


def test_no_airing_advice_when_outdoor_air_is_wetter():
    codes = [x.code for x in advise(_moist(t_out=14.0, rh_out=100.0, t_in=19.0, rh_in=72.0))]
    assert "air_useless" in codes and "air_now" not in codes


def test_airing_minutes_longer_when_excess_small():
    small = next(a for a in advise(_moist(rh_in=62.0, t_out=8.0, rh_out=80.0)) if a.code == "air_now")
    big = next(a for a in advise(_moist(rh_in=75.0, t_out=-5.0, rh_out=80.0)) if a.code == "air_now")
    assert small.params["minutes"] == 10 and big.params["minutes"] == 5


def test_cold_room_gets_minimum_temperature_hint():
    assert "min_temp" in [x.code for x in advise(_moist(t_in=15.5, rh_in=80.0))]


def test_critical_when_mould_index_high_and_manager_notified():
    out = advise(_moist(mould_index=1.4))
    assert out[0].severity == "critical"
    assert "notify_manager" in [x.code for x in out]


def test_data_gap_short_circuits():
    out = advise(_moist(hours_since_data=9))
    assert [x.code for x in out] == ["check_sensor"]


def test_sorted_most_severe_first():
    out = advise(_moist(mould_index=1.2, hours_over_80=30))
    sev = [{"info": 0, "watch": 1, "warn": 2, "critical": 3}[a.severity] for a in out]
    assert sev == sorted(sev, reverse=True)


def test_furniture_hint_after_long_wet_period():
    assert "move_furniture" in [x.code for x in advise(_moist(hours_over_80=30))]


@pytest.mark.parametrize("lang", LANGS)
def test_every_advice_renders_in_every_language(lang):
    for a in advise(_moist(mould_index=1.5, hours_over_80=80, t_in=15.0, rh_in=85.0)):
        txt = a.text(lang)
        assert txt and "{" not in txt


def test_required_frsi_and_surface_rh():
    r = Reading(20.0, 50.0, -5.0, 80.0, 0.70)
    assert required_frsi(r) == pytest.approx(0.70, abs=0.01)
    assert 79.0 < surface_rh_of(r) < 82.0


def test_measured_frsi_overrides_assumed():
    r = Reading(20.0, 50.0, -5.0, 80.0, 0.9, frsi_measured=0.6)
    assert surface_rh_of(r) > 90.0


def test_cli_advise_and_decode(capsys):
    assert main(["advise", "--t-in", "19", "--rh-in", "68", "--t-out", "0", "--rh-out", "85", "--lang", "de"]) == 0
    assert "Lüften" in capsys.readouterr().out
    assert main(["decode", "1109c4"]) == 1  # wrong length is reported, not raised
    assert main(["decode", "zz"]) == 1
