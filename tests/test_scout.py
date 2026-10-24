"""Site Scout tests. They read the saved data/ folder and need no network or key."""
import json

import pytest

import deserts as ds
import scout


@pytest.fixture(scope="module")
def d():
    return ds.load_all()


@pytest.fixture(scope="module")
def tb(d):
    return scout.Toolbox(d, use_llm=False)


def no_llm(messages, tools):
    return None


def test_fallback_picks_worst_county(d):
    out = scout.run_scout(d, "Where should my next diabetes trial site go?", chat=no_llm)
    worst = ds.county_scores(d, "DIABETES")[0].iloc[0]["county"]
    tools = [s["tool"] for s in out["steps"]]
    assert out["mode"] == "offline"
    assert tools == ["rank_counties", "county_details", "simulate_new_site", "write_outreach_flyer"]
    assert out["steps"][0]["result"]["counties"][0]["county"].upper() == worst
    assert all(s["args"].get("county", worst).upper() == worst for s in out["steps"][1:])
    assert not scout.QUALIFY.search(out["answer"])
    assert scout.answer_is_safe(out["answer"], out["steps"])


def test_every_tool_returns_json_serializable_data(tb):
    ranked = tb.run("rank_counties", {"disease": "Diabetes"})
    county = ranked["counties"][0]["county"]
    det = tb.run("county_details", {"county": county, "disease": "Diabetes"})
    hospital = det["top_hospitals"][0]["name"]
    results = [
        ranked, det,
        tb.run("simulate_new_site", {"county": county, "hospital": hospital, "disease": "Diabetes"}),
        tb.run("write_outreach_flyer", {"county": county, "disease": "Diabetes", "language": "English"}),
        tb.run("rank_counties", {"disease": "nonsense"}),  # errors are data too
    ]
    for r in results[:4]:
        assert "error" not in r
    for r in results:
        assert json.loads(json.dumps(r)) == r


def fake_call(i):
    return {"id": f"c{i}", "type": "function", "function": {
        "name": "rank_counties", "arguments": json.dumps({"disease": "Asthma"})}}


def test_agent_stops_at_six_tool_calls(d):
    def greedy(messages, tools):  # always asks for another tool until tools are removed
        if tools:
            return {"role": "assistant", "content": None, "tool_calls": [fake_call(len(messages))]}
        return {"role": "assistant", "content": "Done."}
    out = scout.run_scout(d, "asthma?", chat=greedy)
    assert out["mode"] == "ai" and len(out["steps"]) == scout.MAX_TOOL_CALLS


def test_unsafe_or_invented_answers_are_replaced(d):
    def liar(messages, tools):
        if tools and len(messages) < 3:
            return {"role": "assistant", "content": None, "tool_calls": [fake_call(1)]}
        return {"role": "assistant", "content": "Residents of Hampden qualify for 12345 trials."}
    out = scout.run_scout(d, "asthma?", chat=liar)
    assert "qualify" not in out["answer"] and "12345" not in out["answer"]
