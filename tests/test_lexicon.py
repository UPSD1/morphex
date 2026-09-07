"""Lexicon behaviour.

The lexicon exists to separate a real residue from a chimera. ADEBAYO
legitimately yields BAYO and also yields ADEB, a bad morpheme split;
structure cannot tell them apart, a lexicon can.
"""
import pytest

from morphex import candidates, codes, is_attested, lexicon, normalize


def test_real_short_forms_are_attested():
    for name in ["BAYO", "SEUN", "IFEANYI", "EMEKA", "NGOZI", "MUSA"]:
        assert is_attested(name), f"{name} should be attested"


def test_chimeras_are_not_attested():
    """These are produced by candidate generation and are not names."""
    for junk in ["ADEB", "LUWASEUN", "WASEUN", "YOMIDE", "LOLUWA"]:
        assert not is_attested(junk), f"{junk} should not be attested"


def test_rejected_rows_are_excluded_from_attestation():
    """A row a reviewer marks `rejected` must not count as attested.

    There are currently no rejected rows -- MIDE was the only one and the
    reviewer later confirmed Ayomide does shorten to Mide, so it was
    reinstated. The mechanism still has to work for when one appears, so this
    checks the loader rather than a particular name.
    """
    from morphex.loader import _rows
    raw = _rows("lexicon.tsv")
    rejected = {r["name"].strip().upper() for r in raw
                if r.get("status", "").strip() == "rejected"}
    lex = lexicon()
    for name in rejected:
        assert name not in lex, f"{name} is rejected but still attested"
    assert all(v["status"] != "rejected" for v in lex.values())


def test_attested_only_drops_chimeras_keeps_full_form():
    c = candidates("ADEBAYO", attested_only=True)
    assert "ADEBAYO" in c, "the full form is always retained"
    assert "BAYO" in c, "an attested residue survives"
    assert "ADEB" not in c, "a chimera is dropped"


def test_attested_only_preserves_known_variants():
    assert codes("Ifeanyichukwu", attested_only=True) & codes("Ifeanyi", attested_only=True)
    assert codes("Adebayo", attested_only=True) & codes("Bayo", attested_only=True)


def test_attested_only_is_off_by_default():
    """The lexicon is incomplete, so absence is weak evidence. Filtering by
    default would silently lose real names it does not happen to record."""
    assert "ADEB" in candidates("ADEBAYO")


def test_lexicon_carries_provenance_and_status():
    entry = lexicon()["BAYO"]
    assert entry["provenance"] in {"generator-pool", "common-usage"}
    assert entry["status"] in {"unreviewed", "reviewed"}


def test_lexicon_is_case_insensitive():
    assert is_attested("bayo") and is_attested("Bayo") and is_attested(" BAYO ")


def test_data_files_load_without_treating_data_as_a_package():
    """Regression: the loader used to address ``morphex.data`` as a package.

    ``data/`` has no ``__init__.py``, so it resolves as a namespace package.
    Python 3.10+ tolerates that in ``importlib.resources.files()``; 3.9 does
    not, and CI failed on 3.9 only. This reads every shipped file so the whole
    set is covered rather than whichever one a given test happened to touch.
    """
    from morphex.loader import _rows
    for filename in ("lexicon.tsv", "elements.tsv", "titles.tsv",
                     "hausa_variants.tsv", "arabic_adaptations.tsv"):
        rows = _rows(filename)
        assert rows, f"{filename} loaded no rows"
