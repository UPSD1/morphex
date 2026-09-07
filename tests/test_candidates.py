from morphex import candidates


def test_full_form_always_retained():
    for name in ["IFEOLUWA", "ADEBAYO", "MUSA", "CHUKWUEMEKA"]:
        assert name in candidates(name)


def test_leading_drop_yoruba_pattern():
    assert "BAYO" in candidates("ADEBAYO")
    assert "SEUN" in candidates("OLUWASEUN")


def test_trailing_drop_igbo_pattern():
    assert "IFEANYI" in candidates("IFEANYICHUKWU")
    assert "NGOZI" in candidates("NGOZICHUKWU")
    assert "OBI" in candidates("OBINNA")


def test_ifeoluwa_reaches_its_head_not_its_tail():
    """The motivating case, as the reviewer described it.

    Ifeoluwa is commonly shortened to Ife -- the head. It is not shortened to
    Oluwa: that is a name in its own right, not this person's short form, and
    the Yoruba compound rule suppresses tail elements for exactly that reason.
    """
    c = candidates("IFEOLUWA")
    assert "IFE" in c
    assert "OLUWA" not in c


def test_linker_consonant_is_shed():
    assert "TEMI" in candidates("TEMILOLUWA")


def test_short_names_are_not_shredded():
    assert candidates("MUSA") == {"MUSA"}


def test_initial_vowel_elision():
    assert "LAMIDE" in candidates("OLAMIDE")
    assert "DEBAYO" in candidates("ADEBAYO")


def test_rules_are_individually_toggleable():
    """Each generation rule can be disabled; the ablation in the README
    depends on this."""
    from morphex.candidates import DEFAULT_RULES, ELISION, TRAILING
    assert "DEBAYO" not in candidates("ADEBAYO", rules=DEFAULT_RULES - {ELISION})
    assert "IFEANYI" not in candidates("IFEANYICHUKWU", rules=DEFAULT_RULES - {TRAILING})


def test_longest_element_wins():
    """OLUWASEUN carries OLUWA, not OLU. Stripping the shorter element leaves
    WASEUN, which is not a name anyone uses."""
    c = candidates("OLUWASEUN")
    assert "SEUN" in c
    assert "WASEUN" not in c


def test_derived_forms_are_not_re_derived():
    """Chaining rules produced chimeras: ADEBAYO -> ADEB -> DEB."""
    assert "DEB" not in candidates("ADEBAYO")


def test_bare_elements_are_opt_in():
    """Enabling bare elements collides names sharing an element, so it is off
    by default. Chinedu and Chizoba both reduce to CHI."""
    assert "CHI" not in candidates("CHINEDU")
    assert "CHI" in candidates("CHINEDU", include_bare_elements=True)


def test_hausa_transliteration_group_expands():
    assert "MOHAMMED" in candidates("MUHAMMAD")


def test_empty_is_safe():
    assert candidates("") == set()
