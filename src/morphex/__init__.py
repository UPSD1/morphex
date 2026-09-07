"""morphex -- name matching for Nigerian (Yoruba, Igbo, Hausa) records.

Quick start::

    >>> from morphex import match, codes, explain
    >>> match("Ifeoluwa", "Ife")
    True
    >>> match("Ifeanyichukwu", "Ifeanyi")
    True

The affix inventories that drive this are shipped as reviewable TSV files
under ``morphex/data/`` and are currently marked ``unreviewed``. They have
not been validated by native speakers. See the README before relying on this
for anything consequential.
"""
from .candidates import candidates
from .loader import (elements, is_attested, lexicon, review_status, titles,
                     variant_groups)
from .match import codes, explain, match
from .normalize import fold_diacritics, normalize, strip_titles, tokens
from .phonetics import encode, encode_both

__version__ = "0.1.0"

__all__ = [
    "candidates", "codes", "match", "explain",
    "normalize", "fold_diacritics", "strip_titles", "tokens",
    "encode", "encode_both",
    "elements", "titles", "variant_groups", "review_status",
    "lexicon", "is_attested",
    "__version__",
]
