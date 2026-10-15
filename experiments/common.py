"""Shared paths and helpers for the experiments."""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODELS = os.path.join(ROOT, "models")
UPSTREAM = os.path.join(ROOT, "upstream")
RESULTS = os.path.join(HERE, "results")

sys.path.insert(0, ROOT)


def save(name: str, data) -> str:
    os.makedirs(RESULTS, exist_ok=True)
    path = os.path.join(RESULTS, name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        if name.endswith(".json"):
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        else:
            fh.write(data)
    return path


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def split_frontmatter(text: str) -> tuple[str, str]:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[3:end], text[end + 4:].lstrip("\n")
    return "", text


def h2_sections(body: str) -> list[tuple[str, list[str]]]:
    """Split a Markdown body into (heading, lines) by '## ' headings.

    Lines before the first heading are returned under the heading ''.
    Headings inside fenced code blocks are ignored.
    """
    out: list[tuple[str, list[str]]] = [("", [])]
    fence = False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
        if not fence and re.match(r"^## \S", line):
            out.append((line[3:].strip(), []))
        else:
            out[-1][1].append(line)
    if not any(l.strip() for l in out[0][1]):
        out = out[1:]
    return out


def nonblank(lines) -> int:
    return sum(1 for l in lines if l.strip())


# Token counts use tiktoken's o200k_base encoding as a stand-in for the
# tokenizers of current models (Anthropic's is only available through its API).
# Ratios between two texts depend little on the tokenizer. The encoding file is
# downloaded once and cached by tiktoken.
TOKENIZER = "o200k_base"
_ENC = None


def tokens(text: str) -> int:
    global _ENC
    if _ENC is None:
        import tiktoken
        _ENC = tiktoken.get_encoding(TOKENIZER)
    return len(_ENC.encode(text, disallowed_special=()))
