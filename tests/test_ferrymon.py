"""Offline unit tests for the FerryMon loader cleaning rules (no data files needed)."""
import numpy as np
import pandas as pd

from treestoseas.io.ferrymon import (
    _assign_routes, _combine_datetime, _season, load_ferrymon, _ROUTES,
)


def _write_raw(tmp_path, rows):
    """Write a minimal raw FerryMon CSV (the delivered 13-column schema)."""
    cols = ["cast date", "sample_time", "tempc", "spcond", "salppt",
            "dissolved_o2", "optical_do", "depth_m", "turbid", "chl", "ph",
            "LAT", "LONG"]
    p = tmp_path / "ferrymon_test.csv"
    pd.DataFrame(rows, columns=cols).to_csv(p, index=False)
    return str(p)


def test_combine_datetime_from_strings():
    dt = _combine_datetime(pd.Series(["6/17/2019"]), pd.Series(["13:34:04"]))
    assert dt.iloc[0] == pd.Timestamp("2019-06-17 13:34:04")


def test_season_lookup():
    s = _season(pd.Series([1, 4, 7, 10]))
    assert list(s) == ["winter", "spring", "summer", "fall"]


def test_assign_routes_separates_neuse_from_cape_fear():
    lat = pd.Series([34.95, 33.94, 35.40, 35.11, 0.0])
    lon = pd.Series([-76.81, -77.97, -76.74, -76.15, 0.0])
    route, system = _assign_routes(lat, lon)
    assert list(route) == ["neuse", "cape_fear", "pamlico_river",
                           "pamlico_sound", "other"]
    assert list(system) == ["NR", "CF", "PR", "PS", "other"]


def test_do_negatives_masked_positives_kept(tmp_path):
    rows = [
        ["6/1/2020", "12:00:00", 25, 20, 10, -0.04, 0, 0.1, 5, 3, 7.5, 34.95, -76.81],
        ["6/1/2020", "12:00:30", 25, 20, 10, -8.00, 0, 0.1, 5, 3, 7.5, 34.95, -76.81],
        ["6/1/2020", "12:01:00", 25, 20, 10, 6.20, 0, 0.1, 5, 3, 7.5, 34.95, -76.81],
        ["6/1/2020", "12:01:30", 25, 20, 10, 0.30, 0, 0.1, 5, 3, 7.5, 34.95, -76.81],
        ["6/1/2020", "12:02:00", 25, 20, 10, 25.0, 0, 0.1, 5, 3, 7.5, 34.95, -76.81],
    ]
    df = load_ferrymon(_write_raw(tmp_path, rows))
    do = df["DO_mgL"].tolist()
    assert np.isnan(do[0])         # -0.04 masked (drift, not clamped to 0)
    assert np.isnan(do[1])         # -8 masked (sensor fault)
    assert do[2] == 6.20
    assert do[3] == 0.30           # genuine near-anoxia (small positive) kept
    assert np.isnan(do[4])         # >20 masked
    assert df["DO_mgL"].dtype == "float64"   # NaN-safe dtype even when maskable


def test_ph_zero_sentinel_masked(tmp_path):
    rows = [
        ["6/1/2020", "12:00:00", 25, 20, 10, 6, 0, 0.1, 5, 3, 0.0, 34.95, -76.81],
        ["6/1/2020", "12:00:30", 25, 20, 10, 6, 0, 0.1, 5, 3, 7.8, 34.95, -76.81],
    ]
    df = load_ferrymon(_write_raw(tmp_path, rows))
    assert np.isnan(df["pH"].iloc[0])   # 0.0 -> NaN (probe-off sentinel)
    assert df["pH"].iloc[1] == 7.8


def test_negative_turbidity_and_chl_masked(tmp_path):
    rows = [["6/1/2020", "12:00:00", 25, 20, 10, 6, 0, 0.1, -224, -6.3, 7.5,
             34.95, -76.81]]
    df = load_ferrymon(_write_raw(tmp_path, rows))
    assert np.isnan(df["turbidity_NTU"].iloc[0])
    assert np.isnan(df["chl"].iloc[0])


def test_route_filter_drops_cape_fear(tmp_path):
    rows = [
        ["6/1/2020", "12:00:00", 25, 20, 10, 6, 0, 0.1, 5, 3, 7.5, 34.95, -76.81],
        ["6/1/2020", "12:00:30", 25, 30, 20, 6, 0, 0.1, 5, 3, 7.5, 33.94, -77.97],
    ]
    df = load_ferrymon(_write_raw(tmp_path, rows), route="neuse")
    assert len(df) == 1
    assert df["system"].iloc[0] == "NR"
    assert df["layer"].iloc[0] == "surface"


def test_bad_fix_dropped_and_optical_do_absent(tmp_path):
    rows = [
        ["6/1/2020", "12:00:00", 25, 20, 10, 6, 0, 0.1, 5, 3, 7.5, 0.0, 0.0],
        ["6/1/2020", "12:00:30", 25, 20, 10, 6, 0, 0.1, 5, 3, 7.5, 34.95, -76.81],
    ]
    df = load_ferrymon(_write_raw(tmp_path, rows))
    assert len(df) == 1                       # zero-fix row dropped
    assert "optical_do" not in df.columns     # dead column dropped
    assert "layer" in df.columns and df["layer"].iloc[0] == "surface"
