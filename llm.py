"""One optional LLM call. Returns None on any problem so the app can fall back.

Env vars (no keys in code):
  LLM_PROVIDER   "bedrock", "anthropic" or "groq"
  LLM_MODEL      model id for that provider
  ANTHROPIC_API_KEY   for "anthropic" (called with requests, no SDK needed)
  GROQ_API_KEY        for "groq" (OpenAI-compatible API, called with requests)
  AWS_* credentials   for "bedrock" (needs boto3: pip install boto3)
"""
import contextlib
import contextvars
import os
import re
import time

TIMEOUT = 20  # seconds per attempt
RETRIES = 2  # extra attempts after the first one
RETRY_WAIT = 2  # seconds between attempts when the server gives no hint
MAX_WAIT = 12  # longest we wait for a 429 Retry-After
UNITS = {"ms": 0.001, "s": 1, "m": 60, "h": 3600}
# Optional callback(seconds), called before each wait so a page can tell the user.
# A ContextVar is per script thread, so one Streamlit session never shows another's notice.
on_wait = contextvars.ContextVar("llm_on_wait", default=None)


@contextlib.contextmanager
def notify_waits(callback):
    """While active, callback(seconds) runs before each retry wait in this thread."""
    token = on_wait.set(callback)
    try:
        yield
    finally:
        on_wait.reset(token)
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _anthropic(prompt, system, model):
    import requests

    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"],
                 "anthropic-version": "2023-06-01"},
        json={"model": model, "max_tokens": 800, "system": system,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()["content"][0]["text"]


def _retryable(r):
    """Groq is busy (429), failing (5xx), or the model made a bad tool call (400 tool_use_failed)."""
    return (r.status_code == 429 or r.status_code >= 500
            or (r.status_code == 400 and "tool_use_failed" in r.text))


def _wait_seconds(r):
    """How long to wait before retrying. For a 429: the Retry-After header, else "try again in
    7.6s" (also 340ms, 1m5.2s) from the error body, capped at MAX_WAIT. Otherwise RETRY_WAIT."""
    if r.status_code == 429:
        secs = None
        try:
            secs = float((getattr(r, "headers", None) or {}).get("retry-after"))
        except (TypeError, ValueError):  # missing, or an HTTP date
            pass
        if secs is None:
            m = re.search(r"try again in\s+((?:\d+(?:\.\d+)?(?:ms|h|m|s)\s*)+)", r.text or "", re.I)
            if m:
                secs = sum(float(n) * UNITS[u.lower()]
                           for n, u in re.findall(r"(\d+(?:\.\d+)?)(ms|h|m|s)", m.group(1), re.I))
        if secs is not None:
            return min(max(secs, 0.0), MAX_WAIT)
    return RETRY_WAIT


def _post_groq(body):
    """POST to Groq. Retries up to RETRIES times on retryable errors, then raises on any error."""
    import requests

    for attempt in range(RETRIES + 1):
        r = requests.post(GROQ_URL, headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
                          json=body, timeout=TIMEOUT)
        if attempt < RETRIES and _retryable(r):
            wait = _wait_seconds(r)
            callback = on_wait.get()
            if callback:
                try:
                    callback(wait)
                except Exception:  # a notice must never break the call
                    pass
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()


def _groq(prompt, system, model):
    try:  # fixes Mac SSL errors
        import truststore
        truststore.inject_into_ssl()
    except ImportError:
        pass

    messages = [{"role": "user", "content": prompt}]
    if system:
        messages.insert(0, {"role": "system", "content": system})
    data = _post_groq({"model": model, "max_tokens": 2000, "reasoning_effort": "low",
                       "messages": messages})
    return data["choices"][0]["message"]["content"]


def _bedrock(prompt, system, model):
    import boto3
    from botocore.config import Config

    client = boto3.client("bedrock-runtime", config=Config(
        connect_timeout=TIMEOUT, read_timeout=TIMEOUT, retries={"max_attempts": 0}))
    kwargs = {"modelId": model,
              "messages": [{"role": "user", "content": [{"text": prompt}]}],
              "inferenceConfig": {"maxTokens": 800}}
    if system:
        kwargs["system"] = [{"text": system}]
    out = client.converse(**kwargs)
    return out["output"]["message"]["content"][0]["text"]


def chat_with_tools(messages: list, tools: list) -> dict | None:
    """One chat turn with tool calling (groq only, OpenAI-compatible `tools` param).
    Returns the raw assistant message dict, or None if not configured or on any error."""
    try:
        if os.environ.get("LLM_PROVIDER", "").lower() != "groq":
            return None
        model = os.environ.get("LLM_MODEL", "")
        key = os.environ.get("GROQ_API_KEY", "")
        if not model or not key:
            return None
        try:  # fixes Mac SSL errors
            import truststore
            truststore.inject_into_ssl()
        except ImportError:
            pass

        body = {"model": model, "max_tokens": 2000, "reasoning_effort": "low",
                "messages": messages}
        if tools:
            body.update(tools=tools, tool_choice="auto")
        return _post_groq(body)["choices"][0]["message"]
    except Exception:
        return None


def generate(prompt: str, system: str = "") -> str | None:
    """Return the model text, or None if not configured or anything goes wrong."""
    try:
        provider = os.environ.get("LLM_PROVIDER", "").lower()
        model = os.environ.get("LLM_MODEL", "")
        if not model:
            return None
        if provider == "anthropic":
            text = _anthropic(prompt, system, model)
        elif provider == "groq":
            text = _groq(prompt, system, model)
        elif provider == "bedrock":
            text = _bedrock(prompt, system, model)
        else:
            return None
        return text.strip() or None
    except Exception:
        return None
