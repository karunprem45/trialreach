"""Groq retry tests. requests.post is mocked, so no network or key is needed."""
import pytest
import requests

import llm

GOOD = {"choices": [{"message": {"role": "assistant", "content": "hello"}}]}


class FakeResponse:
    def __init__(self, status, body=None, text="", headers=None):
        self.status_code, self._body, self.text = status, body, text
        self.headers = headers or {}

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


@pytest.fixture
def groq(monkeypatch):
    """Mock requests.post with a queue of responses. Records calls and sleeps."""
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    state = {"queue": [], "calls": [], "sleeps": []}

    def fake_post(url, **kwargs):
        state["calls"].append(kwargs)
        return state["queue"].pop(0)

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(llm.time, "sleep", lambda s: state["sleeps"].append(s))
    return state


def ok():
    return FakeResponse(200, GOOD)


@pytest.mark.parametrize("bad", [
    FakeResponse(429, text="rate limited"),
    FakeResponse(503, text="unavailable"),
    FakeResponse(400, text='{"error":{"code":"tool_use_failed"}}'),
])
def test_chat_with_tools_retries_then_succeeds(groq, bad):
    groq["queue"] = [bad, ok()]
    msg = llm.chat_with_tools([{"role": "user", "content": "hi"}], [])
    assert msg["content"] == "hello"
    assert len(groq["calls"]) == 2
    assert groq["sleeps"] == [2]
    assert all(c["timeout"] == 20 for c in groq["calls"])


def test_chat_with_tools_gives_up_after_two_retries(groq):
    groq["queue"] = [FakeResponse(500), FakeResponse(500), FakeResponse(500)]
    assert llm.chat_with_tools([{"role": "user", "content": "hi"}], []) is None
    assert len(groq["calls"]) == 3  # first try + 2 retries
    assert groq["sleeps"] == [2, 2]


def test_plain_400_is_not_retried(groq):
    groq["queue"] = [FakeResponse(400, text="bad request")]
    assert llm.chat_with_tools([{"role": "user", "content": "hi"}], []) is None
    assert len(groq["calls"]) == 1
    assert groq["sleeps"] == []


def test_generate_via_groq_retries_on_429(groq):
    groq["queue"] = [FakeResponse(429), FakeResponse(429), ok()]
    assert llm.generate("hi", "be brief") == "hello"
    assert len(groq["calls"]) == 3
    assert groq["sleeps"] == [2, 2]


def test_generate_via_groq_returns_none_when_all_attempts_fail(groq):
    groq["queue"] = [FakeResponse(502), FakeResponse(502), FakeResponse(502)]
    assert llm.generate("hi") is None
    assert len(groq["calls"]) == 3


# ---------- 429 waits: Retry-After header or "try again in Xs" in the body ----------
@pytest.mark.parametrize("resp, expected", [
    (FakeResponse(429, headers={"retry-after": "3"}), 3),
    (FakeResponse(429, headers={"retry-after": "1.5"}, text="try again in 9s"), 1.5),  # header wins
    (FakeResponse(429, text="Rate limit reached. Please try again in 7.5s."), 7.5),
    (FakeResponse(429, text="Please try again in 340ms."), 0.34),
    (FakeResponse(429, text="Please try again in 1m5.2s."), 12),  # capped at 12 s
    (FakeResponse(429, headers={"retry-after": "60"}), 12),  # capped at 12 s
    (FakeResponse(429, headers={"retry-after": "Wed, 21 Oct 2026 07:28:00 GMT"}), 2),  # date: default
    (FakeResponse(429, text="no hint here"), 2),
    (FakeResponse(503, headers={"retry-after": "9"}), 2),  # only 429 uses the hint
])
def test_wait_seconds(resp, expected):
    assert llm._wait_seconds(resp) == pytest.approx(expected)


def test_429_waits_as_told_and_notifies(groq):
    groq["queue"] = [FakeResponse(429, headers={"retry-after": "4"}),
                     FakeResponse(429, text="Please try again in 6.5s."), ok()]
    heard = []
    with llm.notify_waits(heard.append):
        msg = llm.chat_with_tools([{"role": "user", "content": "hi"}], [])
    assert msg["content"] == "hello"
    assert groq["sleeps"] == [4, 6.5]
    assert heard == [4, 6.5]
    assert len(groq["calls"]) == 3  # first try + 2 retries


def test_notice_is_off_outside_the_context(groq):
    groq["queue"] = [FakeResponse(429), ok()]
    heard = []
    with llm.notify_waits(heard.append):
        pass
    llm.generate("hi")
    assert heard == []


def test_broken_notice_does_not_break_the_call(groq):
    groq["queue"] = [FakeResponse(429), ok()]

    def boom(seconds):
        raise RuntimeError("ui gone")

    with llm.notify_waits(boom):
        assert llm.generate("hi") == "hello"
