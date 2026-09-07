from morphex import fold_diacritics, normalize, strip_titles, tokens


def test_fold_yoruba_and_igbo_diacritics():
    assert fold_diacritics("Olúwáṣeun") == "Oluwaseun"
    assert fold_diacritics("Ifeọma") == "Ifeoma"
    assert fold_diacritics("Ngọzị") == "Ngozi"


def test_normalize_uppercases_and_strips_punctuation():
    assert normalize("Adebayo.") == "ADEBAYO"
    assert normalize("ade-bayo") == "ADE BAYO"
    assert normalize("  Ade   Bayo  ") == "ADE BAYO"


def test_titles_are_removed():
    assert strip_titles("ALHAJI MUSA") == "MUSA"
    assert normalize("Dr. Chukwuemeka") == "CHUKWUEMEKA"
    assert normalize("Chief Mrs Ngozi") == "NGOZI"


def test_title_like_name_is_not_over_stripped():
    # A name field consisting only of a title yields nothing, not a crash.
    assert normalize("Dr.") == ""


def test_tokens_splits_parts():
    assert tokens("Ifeoluwa Adebayo") == ["IFEOLUWA", "ADEBAYO"]


def test_empty_and_none_safe():
    assert normalize("") == ""
    assert tokens("") == []
