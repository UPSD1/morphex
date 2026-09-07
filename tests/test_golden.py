"""Golden corpus: the behavioural contract of the library.

Any change that flips a row here is a breaking change and must be reflected
in CHANGELOG.md.
"""
import csv
from pathlib import Path

import pytest

from morphex import explain, match

GOLDEN = Path(__file__).parent / "data" / "golden_pairs.tsv"


def _rows():
    lines = [ln for ln in GOLDEN.read_text(encoding="utf-8").splitlines()
             if ln.strip() and not ln.startswith("#")]
    return list(csv.DictReader(lines, delimiter="\t"))


@pytest.mark.parametrize("row", [r for r in _rows() if r.get("status") != "disputed"],
                         ids=lambda r: f"{r['a']}~{r['b']}")
def test_golden_pair(row):
    expected = row["should_match"].strip().lower() == "yes"
    bare = row.get("mode", "default").strip() == "bare"
    actual = match(row["a"], row["b"], include_bare_elements=bare)
    if actual != expected:
        pytest.fail(
            f"{row['a']} ~ {row['b']} ({row['pattern']}): "
            f"expected match={expected}, got {actual}\n"
            f"{explain(row['a'], row['b'], include_bare_elements=bare)}"
        )


def test_corpus_covers_both_directions():
    rows = _rows()
    assert any(r["should_match"] == "yes" for r in rows)
    assert any(r["should_match"] == "no" for r in rows)


def test_corpus_documents_bare_mode_tradeoff():
    """Bare mode must be represented on both sides of its tradeoff.

    The cost side used to be a collision that bare mode caused (Chinedu ~
    Chizoba, both reducing to CHI). The reviewed lexicon now blocks it, so the
    row asserts the block instead.
    """
    bare = [r for r in _rows() if r.get("mode") == "bare"]
    assert any(r["pattern"].startswith("bare-element") for r in bare)
    assert any(r["should_match"] == "no" for r in bare)


def test_corpus_covers_all_three_traditions():
    traditions = {r["tradition"] for r in _rows()}
    assert {"yoruba", "igbo", "hausa"} <= traditions


def test_compound_rule_is_covered_both_ways():
    """The Yoruba compound rule needs head cases and tail cases in the corpus."""
    rows = _rows()
    assert any(r["pattern"] == "compound-head" and r["should_match"] == "yes" for r in rows)
    assert any(r["pattern"] == "compound-tail" and r["should_match"] == "no" for r in rows)
