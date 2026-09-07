from morphex import encode


def test_igbo_ch_onset_is_consistent():
    """Regression: bare Double Metaphone splits CHI- between K and X.

    DM("CHIAMAKA") == "KMK" but DM("CHIOMA") == "XM". Igbo <ch> is a stable
    affricate and must encode identically in both.
    """
    first_letters = {encode(n)[0] for n in
                     ["CHIOMA", "CHIAMAKA", "CHIDERA", "CHIDI", "CHINEDU", "CHUKWU"]}
    assert len(first_letters) == 1, f"inconsistent CH onset: {first_letters}"


def test_known_equivalences_still_hold():
    assert encode("ZAINAB") == encode("ZEINAB")


def test_distinct_names_stay_distinct():
    assert encode("NGOZI") != encode("NNEKA")


def test_empty_is_safe():
    assert encode("") == ""
