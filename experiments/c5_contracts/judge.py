"""LLM judges for C5 obligations (Anthropic, OpenAI, Google).

Each judge receives the same instructions as the human reviewers (see INSTRUCTIONS)
and answers, for each item of results/c5_items.json, whether the guarantees entail
every requirement of the step. Keys and models are read from the environment or from
a .env file at the repository root (see .env.example); providers without a key are
skipped. Answers are cached in results/c5_judge_cache.json, so reruns reproduce them
without keys.

    python experiments/c5_contracts/judge.py            # all providers with a key
    python experiments/c5_contracts/judge.py openai     # one provider

Output: results/c5_judges.json
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from common import RESULTS, ROOT, save  # noqa: E402

CACHE = os.path.join(RESULTS, "c5_judge_cache.json")

sys.path.insert(0, HERE)
from review_text import OVERVIEW, definitions_text  # noqa: E402

INSTRUCTIONS = """You review the contracts between the steps of a software engineering workflow \
that a coding agent carries out with one skill per step. For one step, decide whether its \
guarantees ensure every requirement of the step.

Definitions:
{definitions}

{overview}"""

ITEM = """{step}

Guarantees:
{guarantees}

Requirements of the step:
{requires}

Answer with JSON only: {{"verdict": "entailed" (Ensured) or "not-entailed" (Not ensured), \
"uncovered": [requirements not ensured, word for word]}}"""

PROVIDERS = {
    "anthropic": ("ANTHROPIC_API_KEY", "DEFT_JUDGE_ANTHROPIC_MODEL", "claude-opus-5-5"),
    "openai": ("OPENAI_API_KEY", "DEFT_JUDGE_OPENAI_MODEL", "gpt-5"),
    "google": ("GOOGLE_API_KEY", "DEFT_JUDGE_GOOGLE_MODEL", "gemini-2.5-pro"),
}


def load_env(path: str = os.path.join(ROOT, ".env")) -> None:
    """Set variables from a .env file, without overriding the environment."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            value = value.strip().strip('"').strip("'")
            if value and not os.environ.get(key.strip()):
                os.environ[key.strip()] = value


def step_title(item: dict) -> str:
    if item.get("number"):
        return f"Step {item['number']}: {item['step']}"
    return item["step"][0].upper() + item["step"][1:]


def prompt_for(item: dict) -> str:
    def bullets(xs, indent=""):
        return "\n".join(f"{indent}- {x}" for x in xs) or f"{indent}- (none)"
    guarantees = "\n".join(f"{g['from']}:\n{bullets(g['conditions'], '  ')}" for g in item["guarantee_sources"])
    head = INSTRUCTIONS.format(definitions=definitions_text(), overview=OVERVIEW)
    return head + "\n\n" + ITEM.format(step=step_title(item), guarantees=guarantees or "- (none)",
                                       requires=bullets(item["requires"]))


def _post(url: str, body: dict, headers: dict) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"content-type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.load(resp)


def ask_anthropic(model: str, prompt: str, key: str) -> str:
    body = {"model": model, "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]}
    data = _post("https://api.anthropic.com/v1/messages", body, {"x-api-key": key, "anthropic-version": "2023-06-01"})
    return "".join(c.get("text", "") for c in data["content"] if c.get("type") == "text")


def ask_openai(model: str, prompt: str, key: str) -> str:
    body = {"model": model, "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}}
    data = _post("https://api.openai.com/v1/chat/completions", body, {"authorization": f"Bearer {key}"})
    return data["choices"][0]["message"]["content"]


def ask_google(model: str, prompt: str, key: str) -> str:
    body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json"}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    data = _post(url, body, {"x-goog-api-key": key})
    return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])


ASK = {"anthropic": ask_anthropic, "openai": ask_openai, "google": ask_google}


def parse(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    answer = json.loads(text[start:end + 1])
    verdict = str(answer.get("verdict", "")).strip().lower().replace("_", "-").replace(" ", "-")
    if verdict not in ("entailed", "not-entailed"):
        raise ValueError(f"unexpected verdict: {answer!r}")
    return {"verdict": verdict, "uncovered": [str(u) for u in answer.get("uncovered") or []]}


def items_digest(items: list[dict]) -> str:
    """Fingerprint of the items, so answers are never matched to other items."""
    return hashlib.sha256(json.dumps(items, sort_keys=True).encode()).hexdigest()[:16]


def _key(provider: str, model: str, prompt: str) -> str:
    return hashlib.sha256(json.dumps([provider, model, prompt]).encode()).hexdigest()


def judge(items: list[dict], providers=None) -> dict:
    load_env()
    cache = {}
    if os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as fh:
            cache = json.load(fh)
    out = {}
    for name, (key_var, model_var, default) in PROVIDERS.items():
        if providers and name not in providers:
            continue
        model = os.environ.get(model_var) or default
        key = os.environ.get(key_var)
        answers, missing = {}, 0
        for it in items:
            prompt = prompt_for(it)
            k = _key(name, model, prompt)
            if k not in cache:
                if not key:
                    missing += 1
                    continue
                for attempt in range(3):
                    try:
                        raw = ASK[name](model, prompt, key)
                        cache[k] = {"provider": name, "model": model, "raw": raw, **parse(raw)}
                        break
                    except (urllib.error.URLError, ValueError, KeyError, json.JSONDecodeError) as exc:
                        detail = exc.read().decode()[:300] if isinstance(exc, urllib.error.HTTPError) else str(exc)
                        print(f"{name} {it['id']} attempt {attempt + 1}: {detail}", file=sys.stderr)
                        time.sleep(2 * (attempt + 1))
                with open(CACHE, "w", encoding="utf-8") as fh:
                    json.dump(cache, fh, indent=2)
            if k in cache:
                answers[it["id"]] = {"verdict": cache[k]["verdict"], "uncovered": cache[k]["uncovered"]}
        if answers:
            out[name] = {"model": model, "answers": answers}
        if missing:
            print(f"{name}: no key and {missing} uncached items, skipped", file=sys.stderr)
    return out


def main(providers=None) -> dict:
    with open(os.path.join(RESULTS, "c5_items.json"), encoding="utf-8") as fh:
        items = json.load(fh)
    result = judge(items, providers)
    path = os.path.join(RESULTS, "c5_judges.json")
    if providers and os.path.exists(path):  # keep the other providers' answers
        with open(path, encoding="utf-8") as fh:
            previous = json.load(fh)
        if previous.get("items_digest") == items_digest(items):
            result = {**{k: v for k, v in previous.items() if k != "items_digest"}, **result}
    save("c5_judges.json", {"items_digest": items_digest(items), **result})
    return result


if __name__ == "__main__":
    main(sys.argv[1:] or None)
    with open(os.path.join(RESULTS, "c5_judges.json"), encoding="utf-8") as fh:
        saved = json.load(fh)
    for name, d in saved.items():
        if name != "items_digest":
            print(name, d["model"], len(d["answers"]), "answers")
