"""Redaction helpers for run metadata, trajectory, and artifacts.

Throughput-optimized variant (gen1_peer1 span-slice + batched candidate blob):

1. One lowercased literal scan finds every line that can contain a secret
   (every pattern requires a literal marker).
2. Candidate line *spans* are sliced out of the source text -- no 12k-way
   ``split("\n")`` / ``join`` round trip.
3. Candidate segments are joined with an inert separator (``"\\n,\\x00\\n"``)
   and the ordered pattern pipeline runs once over that compact blob, gated by
   necessary literal conditions.  The separator contains a newline, a comma and
   a NUL, none of which can be crossed by any pattern's character classes, so
   no match can be fabricated at a segment boundary.
4. Line spans are re-spliced into the original text, preserving every byte
   outside candidate lines.

Exactness guards:
* A line whose trailing content could begin a cross-line ``\\s``/value bridge
  causes a fallback to the exact whole-text reference implementation, as does
  an ``api`` at end of line (``api\\s*key`` alternative) and any non-ASCII
  input (``re.IGNORECASE`` performs Unicode case folding that ``str.lower``
  does not reproduce exactly).
"""

from __future__ import annotations

import json
import re
from bisect import bisect_right
from pathlib import Path
from typing import Any

JSONValue = str | int | float | bool | None | list["JSONValue"] | dict[str, "JSONValue"]


_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("bearer_token", re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]{8,}")),
    ("openrouter_key", re.compile(r"\bsk-or-v1-[A-Za-z0-9]{16,}\b")),
    ("orcarouter_key", re.compile(r"\bsk-orca-[A-Za-z0-9]{16,}\b")),
    ("openai_style_key", re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9][A-Za-z0-9._-]{7,}\b")),
    ("github_token", re.compile(r"\bghp_[A-Za-z0-9_]{12,}\b")),
    (
        "named_secret",
        re.compile(
            r"(?i)\b[A-Z0-9_]*(api[_-]?key|auth[_-]?token|access[_-]?token|secret|password)\b"
            r"\s*[:=]\s*['\"]?[^'\"\s,}]{6,}"
        ),
    ),
    (
        "named_secret",
        re.compile(r"(?i)\b(api\s*key|key)\s*`[A-Za-z0-9._~+/=-]{16,}`"),
    ),
    (
        "named_secret",
        re.compile(
            r"(?i)['\"]?\b(api[_-]?key|auth[_-]?token|access[_-]?token|secret|password)\b['\"]?"
            r"\s*[:=]\s*['\"]?[^'\"\s,}]{6,}"
        ),
    ),
)

_SENSITIVE_KEY_RE = re.compile(
    r"(?i)^(api[_-]?key|auth[_-]?token|access[_-]?token|secret|password)$"
)

_REPLACEMENTS: tuple[str, ...] = tuple(
    f"<redacted:{label}>" for label, _pattern in _SECRET_PATTERNS
)

# Every secret pattern requires at least one of these literals (case-folded
# lookup is a superset of the case-sensitive code patterns).
_MARKERS: tuple[str, ...] = (
    "bearer",
    "sk-",
    "ghp_",
    "key",
    "token",
    "secret",
    "password",
)

# A candidate line ending in one of these could start a match that crosses the
# newline through a ``\s`` or ``\s*[:=]\s*`` run; defer to the exact baseline.
_RISKY_TAILS: tuple[str, ...] = (
    "bearer",
    "api",
    "key",
    "token",
    "secret",
    "password",
    ":",
    "=",
    "'",
    '"',
)

# Exact ASCII equivalent of re.search(r"(?i)\bapi\s*\n", text), implemented as
# a cheap literal occurrence walk so a stray "api" inside a token cannot force
# a full 1 MB regex scan.  ``text`` is ASCII-checked by the callers.
_ASCII_WORD = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
# Python ``\s`` on str also matches the ASCII separators \x1c-\x1f.
_ASCII_WS = frozenset(" \t\n\r\v\f\x1c\x1d\x1e\x1f")


def _api_before_newline(low_text: str) -> bool:
    n = len(low_text)
    start = 0
    while True:
        pos = low_text.find("api", start)
        if pos < 0:
            return False
        if pos == 0 or low_text[pos - 1] not in _ASCII_WORD:
            j = pos + 3
            while j < n and low_text[j] in _ASCII_WS:
                j += 1
            # \s* is greedy but may give back a trailing newline; a newline
            # anywhere in the maximal whitespace run satisfies "\s*\n".
            if "\n" in low_text[pos + 3:j]:
                return True
        start = pos + 1


# Necessary conditions for the two named-secret patterns (index 5 and 7).
# Both require a keyword ending in key/token/secret/password, a word boundary,
# then ``\s*[:=]`` (index 7 additionally allows one closing quote).  A cheap
# literal walk over the (much smaller) candidate blob is therefore a sound
# pre-gate: it can only produce false positives, never false negatives.
# ``str.find`` over four literals beats a regex scan of the same blob because
# a regex engine has to try every start position.
_WS = frozenset(" \t\n\r\v\f\x1c\x1d\x1e\x1f")


def _named_gate_flags(low: str) -> tuple[bool, bool]:
    """Return (pattern-5 gate, pattern-7 gate) for ASCII ``low``.

    Pattern 5 needs ``keyword\\b\\s*[:=]``; pattern 7 allows one closing quote
    between the keyword and the whitespace run.  Word-boundary and value-length
    requirements are omitted on purpose: a superset gate is sound.
    """
    n = len(low)
    plain = False
    quoted = False
    for kw in ("key", "token", "secret", "password"):
        start = 0
        while True:
            pos = low.find(kw, start)
            if pos < 0:
                break
            end = pos + len(kw)
            if not plain:
                j = end
                while j < n and low[j] in _WS:
                    j += 1
                if j < n and (low[j] == ":" or low[j] == "="):
                    plain = True
            if not quoted:
                j = end
                if j < n and (low[j] == "'" or low[j] == '"'):
                    j += 1
                while j < n and low[j] in _WS:
                    j += 1
                if j < n and (low[j] == ":" or low[j] == "="):
                    quoted = True
            if plain and quoted:
                return True, True
            start = pos + 1
    return plain, quoted

# Inert segment separator for the batched candidate blob.  NUL/`\n`/`,` cannot
# appear in any token character class and terminate the named-secret value
# class (which excludes ``\s``, quotes, comma and ``}``), so boundary-spanning
# matches are impossible by construction.
_SEP = "\n,\x00\n"


def _redact_full(text: str) -> tuple[str, list[str]]:
    """Exact whole-text reference implementation (sequential patterns)."""
    hits: list[str] = []
    out = text
    for label, pattern in _SECRET_PATTERNS:
        if pattern.search(out):
            hits.append(label)
            out = pattern.sub(f"<redacted:{label}>", out)
    return out, hits


def _candidate_spans(text: str, low_text: str) -> list[tuple[int, int]]:
    """Return sorted (line_start, line_end) spans for marker-bearing lines.

    Occurs in ascending order per marker, so a line already recorded through a
    previous marker is skipped with one bisect instead of re-resolving its
    boundaries (the common corpus case: ``Bearer ... and sk-...`` on one line).
    """
    n = len(text)
    starts: list[int] = []
    ends: list[int] = []
    for marker in _MARKERS:
        start = 0
        while True:
            pos = low_text.find(marker, start)
            if pos < 0:
                break
            i = bisect_right(starts, pos) - 1
            if i >= 0 and pos < ends[i]:
                start = ends[i] + 1
                continue
            line_start = text.rfind("\n", 0, pos) + 1
            line_end = text.find("\n", pos)
            if line_end < 0:
                line_end = n
            if not starts or line_start > starts[-1]:
                starts.append(line_start)
                ends.append(line_end)
            else:
                j = bisect_right(starts, line_start)
                starts.insert(j, line_start)
                ends.insert(j, line_end)
            start = line_end + 1
    return list(zip(starts, ends))


def _gated(index: int, low_blob: str, blob: str,
           ns5: bool = False, ns7: bool = False) -> bool:
    """Necessary literal condition for pattern ``index`` (exact, not heuristic)."""
    if index == 0:  # Bearer ...
        return "bearer" in low_blob
    if index == 1:  # sk-or-v1-...
        return "sk-or-v1-" in low_blob
    if index == 2:  # sk-orca-...
        return "sk-orca-" in low_blob
    if index == 3:  # sk-...
        return "sk-" in low_blob
    if index == 4:  # ghp_...
        return "ghp_" in low_blob
    if index == 5:  # named secret keyword + separator
        return ns5
    if index == 7:  # same, with one optional closing quote before the separator
        return ns7
    # index == 6: "key" plus a backtick-delimited payload
    return "key" in low_blob and "`" in blob


def redact_text(text: str) -> tuple[str, list[str]]:
    """Return redacted text plus the classes of matches found."""
    if not text:
        return text, []
    if not text.isascii():
        # re.IGNORECASE uses Unicode case folding; str.lower() is not a
        # strict superset.  Stay exact on non-ASCII input.
        return _redact_full(text)

    low_text = text.lower()
    spans = _candidate_spans(text, low_text)
    if not spans:
        return text, []

    # Only the named-secret backtick pattern can bridge ``api\\s*key`` across a
    # newline; without any backtick in the text that full-text probe is moot.
    if "`" in text and "api" in low_text and _api_before_newline(low_text):
        return _redact_full(text)

    for line_start, line_end in spans:
        if text[line_start:line_end].rstrip().lower().endswith(_RISKY_TAILS):
            return _redact_full(text)

    segments = [text[s:e] for s, e in spans]
    blob = _SEP.join(segments)
    low_blob = blob.lower()
    ns5, ns7 = _named_gate_flags(low_blob)

    matched = [False] * len(_SECRET_PATTERNS)
    out = blob
    for index, (label, pattern) in enumerate(_SECRET_PATTERNS):
        if not _gated(index, low_blob, blob, ns5, ns7):
            continue
        new_blob, count = pattern.subn(_REPLACEMENTS[index], out)
        if count:
            matched[index] = True
            out = new_blob

    if out is blob:
        return text, []

    new_segments = out.split(_SEP)
    n = len(text)
    parts: list[str] = []
    prev = 0
    for (line_start, line_end), new_segment in zip(spans, new_segments):
        if line_start > prev:
            parts.append(text[prev:line_start])
        parts.append(new_segment)
        if line_end < n:
            parts.append("\n")
            prev = line_end + 1
        else:
            prev = n
    if prev < n:
        parts.append(text[prev:])

    hits = [
        label
        for index, (label, _pattern) in enumerate(_SECRET_PATTERNS)
        if matched[index]
    ]
    return "".join(parts), hits


def redact_json(value: JSONValue) -> tuple[JSONValue, list[str]]:
    """Recursively redact JSON-compatible data."""
    hits: list[str] = []

    def visit(obj: JSONValue) -> JSONValue:
        if isinstance(obj, str):
            redacted, found = redact_text(obj)
            hits.extend(found)
            return redacted
        if isinstance(obj, list):
            return [visit(item) for item in obj]
        if isinstance(obj, dict):
            out: dict[str, JSONValue] = {}
            for key, item in obj.items():
                redacted_key, key_hits = redact_text(str(key))
                hits.extend(key_hits)
                if _SENSITIVE_KEY_RE.match(str(key)):
                    hits.append("named_secret")
                    out[redacted_key] = "<redacted:named_secret>"
                else:
                    out[redacted_key] = visit(item)
            return out
        return obj

    return visit(value), hits


def scan_text(text: str) -> list[str]:
    """Return redaction classes present in text."""
    if not text:
        return []
    if not text.isascii():
        # Unicode case folding (re.IGNORECASE) is not reproducible with
        # str.lower(); keep exact semantics on non-ASCII input.
        return [label for label, pattern in _SECRET_PATTERNS if pattern.search(text)]
    low = text.lower()
    if (
        "bearer" not in low
        and "sk-" not in low
        and "ghp_" not in low
        and "key" not in low
        and "token" not in low
        and "secret" not in low
        and "password" not in low
    ):
        return []
    ns5, ns7 = _named_gate_flags(low)
    hits: list[str] = []
    for index, (label, pattern) in enumerate(_SECRET_PATTERNS):
        if _gated(index, low, text, ns5, ns7) and pattern.search(text):
            hits.append(label)
    return hits


def scan_file(path: Path) -> list[str]:
    """Scan a UTF-8-ish text file for raw secret patterns."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ["unreadable"]
    return scan_text(text)


def dumps_redacted(value: Any, **kwargs: Any) -> str:
    """JSON dump after recursive redaction."""
    redacted, _ = redact_json(value)
    return json.dumps(redacted, ensure_ascii=False, **kwargs)
