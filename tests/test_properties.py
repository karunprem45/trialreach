"""Property-based tests (Hypothesis) for the pure score math and distance."""
import json

import numpy as np
from hypothesis import given, settings, strategies as st

import deserts as ds

# one county = (prevalence %, population, trials in reach)
county = st.tuples(st.floats(1, 40), st.integers(1_000, 1_000_000), st.integers(0, 200))
counties = st.lists(county, min_size=1, max_size=14)


def split(rows):
    affected = [p / 100 * pop for p, pop, _ in rows]
    trials = [t for _, _, t in rows]
    return affected, trials


# Feature: trialreach, Property 1: Scores are in range and the worst county scores 100
@settings(max_examples=100)
@given(counties)
def test_p1_score_range_and_max(rows):
    _, score = ds.desert_score(*split(rows))
    assert ((score >= 0) & (score <= 100)).all()
    assert score.max() == 100


# Feature: trialreach, Property 2: More trials never raise People_Per_Trial
@settings(max_examples=100)
@given(counties, st.integers(0, 13), st.integers(1, 200))
def test_p2_more_trials_not_worse(rows, i, extra):
    i %= len(rows)
    affected, trials = split(rows)
    before, _ = ds.desert_score(affected, trials)
    trials[i] += extra
    after, _ = ds.desert_score(affected, trials)
    assert after[i] <= before[i]


# Feature: trialreach, Property 3: More affected people never lower People_Per_Trial
@settings(max_examples=100)
@given(counties, st.integers(0, 13), st.floats(0, 100_000))
def test_p3_more_affected_not_better(rows, i, extra):
    i %= len(rows)
    affected, trials = split(rows)
    before, _ = ds.desert_score(affected, trials)
    affected[i] += extra
    after, _ = ds.desert_score(affected, trials)
    assert after[i] >= before[i]


# Feature: trialreach, Property 4: Distance is symmetric and zero to itself
lat = st.floats(-90, 90)
lon = st.floats(-180, 180)


@settings(max_examples=100)
@given(lat, lon, lat, lon)
def test_p4_miles_symmetry_identity(a_lat, a_lon, b_lat, b_lon):
    assert np.isclose(ds.miles(a_lat, a_lon, b_lat, b_lon),
                      ds.miles(b_lat, b_lon, a_lat, a_lon))
    assert ds.miles(a_lat, a_lon, a_lat, a_lon) == 0


# Feature: trialreach, Property 5: Trial record JSON round trip
site = st.fixed_dictionaries({
    "facility": st.text(), "city": st.text(),
    "lat": st.floats(-90, 90), "lon": st.floats(-180, 180)})
trial = st.fixed_dictionaries({
    "nct": st.from_regex(r"NCT\d{8}", fullmatch=True),
    "title": st.text(),
    "conditions": st.lists(st.text(), max_size=5),
    "phases": st.lists(st.sampled_from(["PHASE1", "PHASE2", "PHASE3", "NA"]), max_size=2),
    "sites": st.lists(site, max_size=5)})


@settings(max_examples=100)
@given(trial)
def test_p5_trial_json_round_trip(record):
    assert json.loads(json.dumps(record)) == record


# Feature: site-scout, Property 6: Adding a site never increases any county's people_per_trial
_D = ds.load_all()


@settings(max_examples=30, deadline=None)
@given(st.sampled_from(list(ds.CONDITIONS)), st.floats(41.2, 42.9), st.floats(-73.5, -69.9))
def test_p6_new_site_never_hurts(mid, new_lat, new_lon):
    before, after = ds.simulate_new_site(_D, mid, new_lat, new_lon, "Test site")
    b = before.set_index("county")
    a = after.set_index("county").loc[b.index]  # same county order
    assert (a["people_per_trial"] <= b["people_per_trial"] + 1e-9).all()
    assert (a["score"] <= b["score"]).all()
