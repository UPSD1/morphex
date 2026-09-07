"""Rules confirmed by a native-speaker review, 26 Aug 2026 (David Akinboro).

These encode stated linguistic rules rather than inferred ones. A failure here
means the library contradicts a speaker, which is a stronger signal than a
failing heuristic.
"""
import pytest

from morphex import candidates, is_attested, match


class TestAyoHead:
    """A Yoruba name beginning AYO, longer than five letters, shortens to AYO."""

    @pytest.mark.parametrize("name", ["AYOKUNLE", "AYODELE", "AYOOLA", "AYORINDE"])
    def test_ayo_is_a_candidate(self, name):
        assert "AYO" in candidates(name)

    def test_rule_requires_more_than_five_letters(self):
        """AYOKA is five letters, so the rule does not apply to it."""
        assert "AYO" not in candidates("AYOKA")

    def test_ayokunle_shortens_both_ways(self):
        assert match("Ayokunle", "Ayo")
        assert match("Ayokunle", "Kunle")


class TestCompoundNames:
    """Two elements joined are one name, not two.

    OLA is a prefix in its own right and stands alone as a name, so AYOOLA
    must not yield OLA -- that is a different name, not a shortening.
    """

    def test_ayoola_does_not_yield_ola(self):
        assert "OLA" not in candidates("AYOOLA")
        assert not match("Ayoola", "Ola")

    def test_ayoola_still_yields_ayo(self):
        assert match("Ayoola", "Ayo")

    def test_adeife_yields_its_head_not_its_tail(self):
        """Confirmed: people are called by the prefix, not the suffix."""
        assert match("Adeife", "Ade")
        assert not match("Adeife", "Ife")

    @pytest.mark.parametrize("full,head,tail", [
        ("Adeife", "Ade", "Ife"),
        ("Ayoola", "Ayo", "Ola"),
        ("Ifeoluwa", "Ife", "Oluwa"),
    ])
    def test_head_matches_tail_does_not(self, full, head, tail):
        assert match(full, head), f"{full} should shorten to its head {head}"
        assert not match(full, tail), f"{full} should not shorten to its tail {tail}"


class TestLinkerEquivalence:
    """A linking consonant between two elements is optional in writing."""

    def test_adelola_equals_adeola(self):
        assert match("Adelola", "Adeola")


class TestConfirmedShortenings:
    """Pairs confirmed correct by the reviewer."""

    @pytest.mark.parametrize("full,short", [
        ("Adetokunbo", "Tokunbo"),
        ("Afolayan", "Folayan"),
        ("Arinzechukwu", "Arinze"),
        ("Eberechi", "Ebere"),
    ])
    def test_shortens(self, full, short):
        assert match(full, short), f"{full} should match {short}"


class TestNoRegression:
    """Rules added for Yoruba must not break what already worked."""

    @pytest.mark.parametrize("full,short", [
        ("Adebayo", "Bayo"), ("Oluwaseun", "Seun"),
        ("Ifeanyichukwu", "Ifeanyi"), ("Chukwuemeka", "Emeka"),
        ("Muhammad", "Mohammed"), ("Zainab", "Zeinab"),
    ])
    def test_still_matches(self, full, short):
        assert match(full, short)

    @pytest.mark.parametrize("a,b", [
        ("Adebayo", "Adewale"), ("Ngozi", "Nneka"), ("Chinedu", "Chizoba"),
    ])
    def test_still_kept_apart(self, a, b):
        assert not match(a, b)


class TestReviewProvenance:
    def test_reviewed_names_are_attested(self):
        for n in ["ADETOKUNBO", "OLADELE", "CHIDINMA", "AYOKUNLE"]:
            assert is_attested(n)

    @pytest.mark.parametrize("name,tradition", [
        ("ACHIKE", "igbo"), ("ACHOLONU", "igbo"),
        ("ADAKU", "igbo"), ("ANYADIKE", "igbo"),
        ("IBIJOKE", "yoruba"), ("ONAKOYA", "yoruba"),
    ])
    def test_rechecked_labels(self, name, tradition):
        """Six labels initially disagreed with Wikipedia's category and were
        held back. On re-check the reviewer confirmed Wikipedia was right in
        every case, so they are now recorded with the corrected tradition."""
        from morphex import lexicon
        lex = lexicon()
        assert name in lex
        assert lex[name]["tradition"] == tradition
        assert lex[name]["status"] == "reviewed"


class TestArabicAdaptation:
    """The same Arabic root reshaped by different Nigerian languages.

    Hebrew Avraham -> Arabic Ibrahim -> Yoruba Buraimoh. The surface forms
    diverge past anything a phonetic encoder can bridge, so only a table links
    them. Confirmed by David Akinboro, 26 Aug 2026.
    """

    def test_ibrahim_matches_buraimoh(self):
        assert match("Ibrahim", "Buraimoh")
        assert match("Buraimoh", "Ibrahim")

    def test_phonetic_encoding_alone_would_never_link_them(self):
        """Establishes why the table is necessary rather than redundant."""
        from morphex import encode
        assert encode("IBRAHIM") != encode("BURAIMOH")

    def test_adaptation_does_not_over_link(self):
        assert not match("Ibrahim", "Yusuf")
        assert not match("Buraimoh", "Bello")
