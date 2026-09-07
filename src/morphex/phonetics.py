"""Phonetic encoding tuned for Nigerian names.

Double Metaphone is the base encoder, but it carries rules from European
languages that misfire on Nigerian orthography. The measured problem:

    DM("CHIAMAKA") -> "KMK"      (Italian/Greek CHI -> K rule fires)
    DM("CHIOMA")   -> "XM"       (default CH -> X)

Same Igbo <ch> onset, two different consonant codes. Igbo <ch> is a stable
/tʃ/ and must never split like that. Rewriting <ch> as <tch> before encoding
forces the default branch and makes the onset consistent:

    encode("CHIAMAKA") -> "XMK"
    encode("CHIOMA")   -> "XM"
"""
from __future__ import annotations

import re
from typing import Optional

from metaphone import doublemetaphone

_CH = re.compile(r"CH")


def _pre(name: str) -> str:
    """Orthographic fixes applied before Double Metaphone."""
    return _CH.sub("TCH", name)


def encode(name: str) -> str:
    """Primary phonetic code for a normalized name. '' if not encodable."""
    if not name:
        return ""
    return doublemetaphone(_pre(name))[0] or ""


def encode_both(name: str) -> tuple:
    """(primary, alternate) codes. Alternate is usually empty for these names."""
    if not name:
        return ("", "")
    return doublemetaphone(_pre(name))
