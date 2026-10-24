"""One optional LLM call. Returns None on any problem so the app can fall back.

Env vars (no keys in code):
  LLM_PROVIDER   "bedrock", "anthropic" or "groq"
  LLM_MODEL      model id for that provider
  ANTHROPIC_API_KEY   for "anthropic" (called with requests, no SDK needed)
  GROQ_API_KEY        for "groq" (OpenAI-compatible API, called with requests)
  AWS_* credentials   for "bedrock" (needs boto3: pip install boto3)
"""
import os

TIMEOUT = 20  # seconds


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


def _groq(prompt, system, model):
    import requests

    try:  # fixes Mac SSL errors
        import truststore
        truststore.inject_into_ssl()
    except ImportError:
        pass

    messages = [{"role": "user", "content": prompt}]
    if system:
        messages.insert(0, {"role": "system", "content": system})
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
        json={"model": model, "max_tokens": 800, "messages": messages},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


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
