"""Public matching API."""
from __future__ import annotations

from typing import Dict, List, Set

from .candidates import candidates
from .loader import is_attested
from .normalize import normalize, tokens
from .phonetics import encode


def codes(name: str, include_bare_elements: bool = False, rules=None,
          attested_only: bool = False) -> Set[str]:
    """Phonetic codes for every plausible surface form of ``name``.

    NOTE: ``codes()`` sees one name, so it cannot apply the pairwise guard in
    ``match()`` that rejects a collision between two distinct attested names.
    ``match("Ayoola", "Ola")`` is False; ``codes("Ayoola") & codes("Ola")`` is
    non-empty, because both reduce to "AL" and only a pair comparison can tell
    that they are separate names rather than a name and its short form.

    This matters when codes are precomputed. A caller that builds a key or an
    index entry per record, before it knows what that record will be compared
    against, cannot apply the guard, and the collision reaches the key. Callers
    that can compare pairs should use ``match()``. Callers that cannot should
    bind independent evidence alongside the name code, which is what suppresses
    the collision in practice.

    Multi-word input is handled part-wise; the union of all parts' codes is
    returned, so "Ifeoluwa Adebayo" matches either "Ifeoluwa" or "Adebayo".
    """
    out: Set[str] = set()
    for part in tokens(name):
        kw = {'attested_only': attested_only}
        if rules is not None:
            kw['rules'] = rules
        for cand in candidates(part, include_bare_elements, **kw):
            c = encode(cand)
            if c:
                out.add(c)
    return out


def _distinct_attested(a: str, b: str, include_bare_elements: bool) -> bool:
    """True when a and b are two different attested names with no rule linking them.

    Double Metaphone discards most vowel information, which collapses
    vowel-heavy Yoruba names onto each other: AYOOLA and OLA both encode to
    "AL". The candidate rules correctly refuse to derive OLA from AYOOLA --
    they are separate names, not a name and its short form -- but the codes
    collide anyway, so the phonetic layer alone cannot keep them apart.

    The reviewed lexicon can. If both forms are attested names, and neither is
    reachable from the other by any generation rule, the collision is an
    artefact of the encoder rather than evidence of a shared identity. Reject
    it. ADETOKUNBO and TOKUNBO are both attested too, but TOKUNBO *is* a
    derived candidate of ADETOKUNBO, so that pair survives.
    """
    na, nb = normalize(a), normalize(b)
    if not na or not nb or na == nb:
        return False
    if " " in na or " " in nb:
        return False
    if not (is_attested(na) and is_attested(nb)):
        return False
    return (nb not in candidates(na, include_bare_elements)
            and na not in candidates(nb, include_bare_elements))


def match(a: str, b: str, include_bare_elements: bool = False) -> bool:
    """True if two names share any phonetic code.

    This is a *recall-oriented* primitive. Names are not unique, so it is
    designed to be combined with other evidence rather than used as a
    standalone identity decision.
    """
    if _distinct_attested(a, b, include_bare_elements):
        return False
    ca = codes(a, include_bare_elements)
    if not ca:
        return False
    return bool(ca & codes(b, include_bare_elements))


def explain(a: str, b: str, include_bare_elements: bool = False) -> Dict[str, object]:
    """Human-readable account of why two names did or did not match.

    Intended for anyone who has to justify a match: a reviewer confirming an
    affix rule, or an audit trail explaining why two records were joined,
    needs to see which candidate form produced the collision.
    """
    na, nb = normalize(a), normalize(b)
    ca, cb = codes(a, include_bare_elements), codes(b, include_bare_elements)
    shared = ca & cb

    def trace(name: str) -> List[dict]:
        rows = []
        for part in tokens(name):
            for cand in sorted(candidates(part, include_bare_elements)):
                rows.append({"part": part, "candidate": cand, "code": encode(cand)})
        return rows

    return {
        "input": {"a": a, "b": b},
        "normalized": {"a": na, "b": nb},
        "matched": bool(shared),
        "shared_codes": sorted(shared),
        "codes": {"a": sorted(ca), "b": sorted(cb)},
        "derivation": {"a": trace(a), "b": trace(b)},
    }
