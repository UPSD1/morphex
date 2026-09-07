"""Loading of the reviewable TSV inventories that ship with the package."""
from __future__ import annotations

import csv
from functools import lru_cache
from importlib.resources import files
from typing import Dict, FrozenSet, List, Tuple


def _rows(filename: str) -> List[dict]:
    """Read a shipped TSV, skipping '#' comment lines.

    Anchored on the ``morphex`` package and navigated into ``data`` as a
    directory, rather than addressing ``morphex.data`` as a package. The data
    directory has no ``__init__.py``, so it resolves as a namespace package.
    Python 3.10+ tolerates that; 3.9 does not, and raised at import time on
    every call. Anchoring on the real package works on every supported version.
    """
    text = (files("morphex") / "data" / filename).read_text(encoding="utf-8")
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
    return list(csv.DictReader(lines, delimiter="\t"))


@lru_cache(maxsize=None)
def elements() -> Dict[str, dict]:
    """Name elements keyed by uppercase element string."""
    out = {}
    for r in _rows("elements.tsv"):
        el = r["element"].strip().upper()
        if el:
            out[el] = {
                "tradition": r.get("tradition", "").strip(),
                "position": r.get("position", "both").strip() or "both",
                "gloss": r.get("gloss", "").strip(),
                "status": r.get("status", "unreviewed").strip(),
            }
    return out


@lru_cache(maxsize=None)
def leading_elements() -> FrozenSet[str]:
    return frozenset(e for e, m in elements().items() if m["position"] in ("leading", "both"))


@lru_cache(maxsize=None)
def trailing_elements() -> FrozenSet[str]:
    return frozenset(e for e, m in elements().items() if m["position"] in ("trailing", "both"))


@lru_cache(maxsize=None)
def titles() -> FrozenSet[str]:
    return frozenset(r["title"].strip().upper() for r in _rows("titles.tsv") if r.get("title"))


@lru_cache(maxsize=None)
def variant_groups() -> Tuple[FrozenSet[str], ...]:
    """Equivalence groups: transliteration spread and cross-tradition adaptation.

    Two files feed this. ``hausa_variants.tsv`` holds spelling variation of one
    name within a tradition (MUHAMMAD / MOHAMMED). ``arabic_adaptations.tsv``
    holds the same Arabic root reshaped by different Nigerian languages
    (IBRAHIM / BURAIMOH), where the surface forms diverge far enough that no
    phonetic method connects them.
    """
    groups = []
    for filename, column in (("hausa_variants.tsv", "group"),
                             ("arabic_adaptations.tsv", "group")):
        for r in _rows(filename):
            members = [m.strip().upper() for m in r[column].split("|") if m.strip()]
            if len(members) > 1:
                groups.append(frozenset(members))
    return tuple(groups)


@lru_cache(maxsize=None)
def variant_lookup() -> Dict[str, FrozenSet[str]]:
    """Map each variant member to its full equivalence group."""
    out = {}
    for g in variant_groups():
        for m in g:
            out[m] = g
    return out


def review_status() -> Dict[str, int]:
    """Counts of reviewed vs unreviewed inventory rows, for audit reporting."""
    counts = {"reviewed": 0, "unreviewed": 0}
    for m in elements().values():
        counts[m["status"]] = counts.get(m["status"], 0) + 1
    return counts


@lru_cache(maxsize=None)
def lexicon() -> Dict[str, dict]:
    """Attested Nigerian name forms, keyed by uppercase name.

    Rows marked ``rejected`` are excluded: a reviewer has confirmed the form
    is not in use, so treating it as attested would be worse than not having
    it at all.
    """
    out = {}
    for r in _rows("lexicon.tsv"):
        name = r["name"].strip().upper()
        if not name or r.get("status", "").strip() == "rejected":
            continue
        out[name] = {
            "tradition": r.get("tradition", "").strip(),
            "type": r.get("type", "").strip(),
            "provenance": r.get("provenance", "").strip(),
            "status": r.get("status", "unreviewed").strip(),
        }
    return out


def is_attested(name: str) -> bool:
    """True if ``name`` is a recorded Nigerian name form.

    Absence is weak evidence: the lexicon is incomplete, so an unattested
    form may be a real name nobody has recorded yet rather than a chimera.
    """
    return bool(name) and name.strip().upper() in lexicon()
