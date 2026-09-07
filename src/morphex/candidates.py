"""Affix-aware candidate generation.

The conventional approach strips one leading affix and commits to the
residue. That is correct for the Yoruba pattern, where the short form is a
SUFFIX of the full name:

    Adebayo -> Bayo          (drop the head)

and backwards for the Igbo pattern, where the short form is a PREFIX:

    Ifeanyichukwu -> Ifeanyi (drop the tail)

Committing to one guess loses the other pattern. This module refuses to
commit: it returns the SET of plausible surface forms and lets the matcher
decide. The full form is always retained, so precision cannot collapse onto
the residues alone.
"""
from __future__ import annotations

from typing import Set

from .loader import (elements, is_attested, leading_elements,
                     trailing_elements, variant_lookup)

#: Candidates shorter than this are dropped as too generic to match on.
MIN_CANDIDATE_LEN = 3

#: Consonants that survive on the head when a trailing element is removed.
#: Temiloluwa segments as TEMI + l + OLUWA, leaving "TEMIL"; the short form
#: people actually use is "Temi".
LINKERS = frozenset("LRNMW")

#: Word-initial vowels that elide in informal usage (Olamide -> Lamide).
VOWELS = frozenset("AEIOU")

#: Reviewed rule, Yoruba. A name beginning AYO and longer than five letters
#: shortens to AYO regardless of what follows, so AYO survives the compound
#: suppression below that would otherwise remove it.
#:
#:     AYOKUNLE -> AYO  and  KUNLE
#:     AYOOLA   -> AYO  but NOT OLA
#:
#: Confirmed by David Akinboro, 26 Aug 2026.
AYO_MIN_LEN = 6

#: Individually toggleable generation rules. Each is measured separately in
#: the ablation table in the README: enabling a rule buys variant recall and
#: costs collisions, and the trade is different for each one.
LEADING = "leading"        # Adebayo -> Bayo
TRAILING = "trailing"      # Ifeanyichukwu -> Ifeanyi
LINKER = "linker"          # Temiloluwa -> Temi (sheds the joining consonant)
ELISION = "elision"        # Olamide -> Lamide (initial vowel only)
TRANSLIT = "translit"      # Muhammad -> Mohammed
COMPOUND = "compound"      # Adeife stays Adeife; Ayoola does not yield Ola
AYO_HEAD = "ayo_head"      # Ayokunle -> Ayo

ALL_RULES = frozenset({LEADING, TRAILING, LINKER, ELISION, TRANSLIT,
                       COMPOUND, AYO_HEAD})

#: Rules enabled by default: all of them. This library is recall-oriented by
#: design (see ``match``), so the default favours finding variants and leaves
#: precision to the caller's other evidence.
#:
#: ELISION is the one genuinely marginal rule. Measured on 122 real Nigerian
#: names it buys 2 more variant pairs and costs 5 points of collision rate,
#: because it also fires where the elided form is not a name anyone uses
#: (OLUWASEUN -> LUWASEUN, IFEANYICHUKWU -> FEANYICHUKWU). It is on by default
#: because Adebayo ~ Debayo is a documented Nigerian pattern and because a
#: caller binding date of birth and sex sees those collisions filtered out.
#: If you are matching names in isolation, drop it:
#:
#:     candidates(name, rules=DEFAULT_RULES - {ELISION})
#:
#: Restricting elision to cases a native speaker confirms is the top item on
#: the linguistic review list.
DEFAULT_RULES = ALL_RULES


def _strip_leading(word, elements):
    """Longest matching leading element only. Returns (residue, element) or None.

    Longest-match matters: OLUWASEUN carries OLUWA, not OLU. Stripping the
    shorter element leaves WASEUN, which is not a name anyone uses.
    """
    best = None
    for el in elements:
        if word.startswith(el) and len(word) > len(el):
            if best is None or len(el) > len(best):
                best = el
    if best is None:
        return None
    residue = word[len(best):]
    return (residue, best) if len(residue) >= MIN_CANDIDATE_LEN else None


def _strip_trailing(word, elements):
    """Longest matching trailing element only. Returns (head, element) or None."""
    best = None
    for el in elements:
        if word.endswith(el) and len(word) > len(el):
            if best is None or len(el) > len(best):
                best = el
    if best is None:
        return None
    head = word[: -len(best)]
    return (head, best) if len(head) >= MIN_CANDIDATE_LEN else None


def candidates(name: str, include_bare_elements: bool = False,
               rules=DEFAULT_RULES, attested_only: bool = False) -> Set[str]:
    """Plausible surface forms for a single normalized name part.

    Args:
        name: an already-normalized, uppercase, single-word name.
        rules: which generation rules to apply. See ``ALL_RULES``.
        attested_only: drop derived candidates that are not in the shipped
            name lexicon. The full form is always kept. This trades recall
            for precision and is the single most effective control on the
            collision rate; see the ablation table in the README.
        include_bare_elements: also emit the element itself, so that
            Chidera -> Chi is reachable. **Off by default**: on its own this
            collides every name sharing an element (Chinedu ~ Chizoba both
            reduce to CHI). Measured on 122 real Nigerian names it raises the
            collision rate from 25% to 45%. Safe to enable only when the
            caller binds independent evidence such as date of birth and sex,
            as record-linkage tokens do.

    Returns:
        Set of candidate forms, always including ``name`` itself.

    Generation is deliberately shallow. Each candidate is at most one leading
    strip, one trailing strip, or one initial-vowel elision away from the
    original, and derived forms are never re-derived from. Chaining rules
    produced chimeras that are not names in any tradition: ADEBAYO yielded
    ADEB (a bad split, since the AYO in BAYO is not a suffix morpheme) and
    then DEB (vowel elision applied to that bad split).
    """
    if not name:
        return set()

    lead = leading_elements()
    trail = trailing_elements()
    out = {name}

    # One leading strip: Adebayo -> Bayo, Chukwuemeka -> Emeka
    head_strip = _strip_leading(name, lead) if LEADING in rules else None
    if head_strip:
        out.add(head_strip[0])

    # One trailing strip: Ifeanyichukwu -> Ifeanyi, Ngozichukwu -> Ngozi
    tail_strip = _strip_trailing(name, trail) if TRAILING in rules else None
    if tail_strip:
        residue = tail_strip[0]
        out.add(residue)
        # Shed a linking consonant: Temiloluwa -> TEMIL -> TEMI
        if (LINKER in rules and len(residue) > MIN_CANDIDATE_LEN
                and residue[-1] in LINKERS):
            trimmed = residue[:-1]
            if len(trimmed) >= MIN_CANDIDATE_LEN:
                out.add(trimmed)

    # Initial-vowel elision, applied ONLY to the original name.
    if ELISION in rules and name[0] in VOWELS and len(name) - 1 >= MIN_CANDIDATE_LEN:
        out.add(name[1:])

    if include_bare_elements:
        if head_strip:
            el = head_strip[1]
            if len(el) >= MIN_CANDIDATE_LEN:
                out.add(el)

    # Compound names of two elements are one name, not two.
    #
    # OLA is a prefix in its own right and also stands alone as a name, so
    # AYOOLA must not be split into OLA -- the residue is not a shortening of
    # this person's name, it is a different name that happens to appear at the
    # end of it. The same holds for ADEIFE, which is Adeife and not Ade or Ife.
    #
    # The rule is therefore: never emit a residue that is itself a known
    # element. Confirmed by David Akinboro, 26 Aug 2026.
    if COMPOUND in rules:
        # Yoruba only, and TAIL residues only.
        #
        # Stated rule: AYOOLA does not shorten to OLA, because OLA is a prefix
        # in its own right and a name in its own right -- the tail of a
        # compound is a different name, not a shortening of this one.
        #
        # The HEAD is left alone, because the head is exactly what people use:
        # AYOOLA -> AYO and IFEOLUWA -> IFE were both given as real usage.
        #
        # Confirmed 26 Aug 2026: people are called by the prefix, not the
        # suffix. ADEIFE, AYOOLA and IFEOLUWA all shorten -- to ADE, AYO and
        # IFE respectively, never to IFE, OLA or OLUWA.
        #
        # Igbo is excluded: OBI is an element and also a real short form of
        # OBINNA, CHI likewise for CHIDERA.
        els = elements()
        yoruba_els = {e for e, meta in els.items()
                      if meta["tradition"] in ("yoruba", "both")}
        tails = {e for e in yoruba_els
                 if name.endswith(e) and len(name) > len(e)}
        if tails:
            out = {c for c in out if c == name or c not in tails}

    # ...except AYO, which is explicitly attested as a short form for any
    # AYO-initial name over five letters.
    if AYO_HEAD in rules and name.startswith("AYO") and len(name) >= AYO_MIN_LEN:
        out.add("AYO")

    # A linking consonant between two elements is optional in the written
    # form: ADELOLA and ADEOLA are the same name. Emit the unlinked form.
    if LINKER in rules:
        lead_all = leading_elements()
        for el in lead_all:
            if not name.startswith(el):
                continue
            rest = name[len(el):]
            if len(rest) > 1 and rest[0] in LINKERS and rest[1:] in lead_all:
                out.add(el + rest[1:])

    # Drop residues that are not names anyone uses. ADEBAYO legitimately
    # yields BAYO and also yields ADEB, a bad morpheme split; structure
    # cannot separate them but the lexicon can.
    if attested_only:
        out = {c for c in out if c == name or is_attested(c)}

    # Transliteration variants (Hausa / Arabic-derived): Muhammad ~ Mohammed.
    if TRANSLIT in rules:
        lookup = variant_lookup()
        for form in list(out):
            if form in lookup:
                out |= set(lookup[form])

    return out
