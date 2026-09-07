"""Surface normalization for Nigerian name fields.

Handles what actually turns up in a name column: mixed case, embedded
honorifics, punctuation, and Yoruba/Igbo diacritics that are recorded
inconsistently or not at all.
"""
from __future__ import annotations

import re
import unicodedata
from typing import List

from .loader import titles

_NON_ALPHA = re.compile(r"[^A-Z ]+")
_WS = re.compile(r"\s+")


def fold_diacritics(text: str) -> str:
    """Drop combining marks: 'Olúwáṣeun' -> 'Oluwaseun'.

    Yoruba tone marks and Igbo sub-dots carry real linguistic information,
    but most systems record them inconsistently or not at all. Folding is the
    only defensible choice for matching; it is lossy and deliberate.
    """
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    # Handle characters with no combining decomposition.
    stripped = stripped.replace("ɳ", "n").replace("ŋ", "n")
    return unicodedata.normalize("NFC", stripped)


def strip_titles(name: str) -> str:
    """Remove honorifics that get typed into name fields."""
    parts = [p for p in name.split() if p and p.rstrip(".") not in titles()]
    return " ".join(parts)


def normalize(name: str) -> str:
    """Full normalization: fold, uppercase, de-title, strip punctuation."""
    if not name:
        return ""
    out = fold_diacritics(str(name)).upper()
    out = out.replace("-", " ").replace("'", "").replace("’", "")
    out = _NON_ALPHA.sub(" ", out)
    out = strip_titles(out)
    return _WS.sub(" ", out).strip()


def tokens(name: str) -> List[str]:
    """Normalized name split into whitespace-separated parts."""
    n = normalize(name)
    return n.split() if n else []
