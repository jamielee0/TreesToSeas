"""Offline unit tests for the Program 195 loader logic (no network)."""
import pandas as pd

from treestoseas.io.program195 import _strip_excel, annual_cpue_index, SPECIES_KEY


def test_strip_excel_qualifier():
    assert _strip_excel('="Pamlico Sound Survey"') == "Pamlico Sound Survey"
    assert _strip_excel('="000879300"') == "000879300"
    assert _strip_excel("23.9") == "23.9"      # bare numerics untouched
    assert _strip_excel(None) is None


def test_species_key_map():
    assert SPECIES_KEY["CALLINECTES SAPIDUS"] == "blue_crab"
    assert SPECIES_KEY["MICROPOGONIAS UNDULATUS"] == "atlantic_croaker"


def test_annual_cpue_index_handles_zero_catch_effort():
    # year 2000: two tows (effort 2 each => total effort 4); crab caught in only one (10 fish)
    df = pd.DataFrame({
        "COLLECTIONNUMBER": ["A", "A", "B"],
        "YEAR": [2000, 2000, 2000],
        "EFFORT": [2.0, 2.0, 2.0],
        "NUMBERTOTAL": [10.0, 5.0, 0.0],
        "species_key": ["blue_crab", "atlantic_croaker", None],
        "SPECIESSCIENTIFICNAME": ["CALLINECTES SAPIDUS", "MICROPOGONIAS UNDULATUS", None],
        "LOCATION": ["NEUSE RIVER", "NEUSE RIVER", "NEUSE RIVER"],
    })
    idx = annual_cpue_index(df, value="NUMBERTOTAL")
    crab = idx[idx.species_key == "blue_crab"].iloc[0]
    # total effort = sum over UNIQUE tows (A, B) = 4; crab total = 10 -> cpue 2.5
    assert crab["total_effort"] == 4.0
    assert crab["cpue"] == 2.5


def test_annual_cpue_index_location_filter():
    df = pd.DataFrame({
        "COLLECTIONNUMBER": ["A", "B"], "YEAR": [2001, 2001], "EFFORT": [1.0, 1.0],
        "NUMBERTOTAL": [4.0, 8.0], "species_key": ["blue_crab", "blue_crab"],
        "SPECIESSCIENTIFICNAME": ["CALLINECTES SAPIDUS"] * 2,
        "LOCATION": ["NEUSE RIVER", "PAMLICO SOUND; EAST OF BLUFF SHOAL"],
    })
    only_neuse = annual_cpue_index(df, locations=["NEUSE RIVER"])
    assert only_neuse.iloc[0]["total_effort"] == 1.0   # only tow A counts
    assert only_neuse.iloc[0]["cpue"] == 4.0
