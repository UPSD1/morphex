from morphex import codes, explain, match, review_status


def test_match_is_symmetric():
    assert match("Ifeoluwa", "Ife") == match("Ife", "Ifeoluwa")


def test_explain_reports_shared_code():
    result = explain("Ifeanyichukwu", "Ifeanyi")
    assert result["matched"] is True
    assert result["shared_codes"]
    assert result["derivation"]["a"]


def test_multiword_matches_on_any_part():
    assert match("Ifeoluwa Adebayo", "Bayo")


def test_codes_never_contains_empty_string():
    assert "" not in codes("Ifeoluwa")


def test_review_status_is_reported():
    """The inventories ship unreviewed; callers must be able to detect that."""
    status = review_status()
    assert "unreviewed" in status
