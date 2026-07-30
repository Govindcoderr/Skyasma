from __future__ import annotations

import json
import re
from typing import Any


class OutputParseError(Exception):
    """Raised when the LLM output cannot be parsed as JSON."""


_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
_JSON_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)


def parse_json(raw: str) -> dict[str, Any]:
    """Best-effort JSON extraction: clean JSON, fenced JSON, or JSON embedded in prose."""
    candidates = [raw.strip()]

    fenced = _FENCE_RE.search(raw)
    if fenced:
        candidates.insert(0, fenced.group(1).strip())

    obj_match = _JSON_OBJ_RE.search(raw)
    if obj_match:
        candidates.append(obj_match.group(0))

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    raise OutputParseError(f"Could not parse JSON from LLM output:\n\n{raw}")