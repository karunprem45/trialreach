"""Unit tests U1-U7. They read the saved data/ folder and need no network."""
import pytest

import deserts as ds
import llm


@pytest.fixture(scope="module")
def d():
    return ds.load_all()


@pytest.fixture(scope="module")
def scores(d):
    return {m: ds.county_scores(d, m) for m in ds.CONDITIONS}


def test_u1_boston_to_springfield_miles():
    assert 75 <= ds.miles(42.36, -71.06, 42.10, -72.59) <= 85


def test_u2_fourteen_counties_per_disease(scores):
    for mid, (counties, _, _) in scores.items():
        assert len(counties) == 14, mid


def test_u3_scores_in_range_and_worst_is_100(scores):
    for mid, (counties, _, _) in scores.items():
        assert counties["score"].between(0, 100).all(), mid
        assert counties["score"].max() == 100, mid


def test_u4_no_missing_values(d, scores):
    for mid, (counties, towns, _) in scores.items():
        assert counties["prevalence"].notna().all(), mid
        assert towns["nearest_miles"].notna().all(), mid


def test_u5_detail_functions_run_for_every_county(d, scores):
    for mid, (counties, _, sites) in scores.items():
        state_prev = ds.state_prevalence(counties)
        for _, row in counties.iterrows():
            hospitals = ds.candidate_hospitals(d, row["county"], sites)
            ej_pop, ej_towns = ds.ej_summary(d, row["county"])
            brief = ds.outreach_brief(ds.CONDITIONS[mid], row, state_prev,
                                      hospitals, ej_pop, ej_towns)
            assert brief.strip(), (mid, row["county"])


def test_u6_hampden_diabetes_gap_over_10x(scores):
    ppt = scores["DIABETES"][0].set_index("county")["people_per_trial"]
    assert ppt["HAMPDEN"] > 10 * ppt["SUFFOLK"]


def test_u7_generate_returns_none_without_env(monkeypatch):
    for var in ("LLM_PROVIDER", "LLM_MODEL", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    assert llm.generate("hello") is None

def test_u8_simulate_new_site_columns_and_effect(d, scores):
    counties, _, sites = scores["DIABETES"]
    worst = counties.iloc[0]
    hosp = ds.candidate_hospitals(d, worst["county"], sites).dropna(subset=["lat", "lon"]).iloc[0]
    before, after = ds.simulate_new_site(d, "DIABETES", float(hosp["lat"]), float(hosp["lon"]), "Test")
    assert len(before) == len(after) == 14
    for df in (before, after):
        assert {"rank", "newly_reached"} <= set(df.columns)
    assert before["county"].tolist() == counties["county"].tolist()
    assert (before["newly_reached"] == 0).all()
    assert after["newly_reached"].sum() >= 0
    assert after["score"].max() <= 100
