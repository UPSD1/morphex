# morphex

Affix-aware normalization, candidate generation and phonetic matching for
Nigerian personal names — Yoruba, Igbo and Hausa.

Wherever a system has to decide whether two records name the same person,
Nigerian names break the usual tools. `Ifeoluwa` and `Ife` are the same person.
So are `Adebayo` and `Bayo`, `Ifeanyichukwu` and `Ifeanyi`, `Muhammad` and
`Mohammed`. Soundex, Double Metaphone and Jaro-Winkler catch none of them.

That problem shows up in deduplicating a customer database, searching a
registry, resolving identities across systems, matching a name against a
watchlist, or linking records without exposing them. The library does not
assume any of those; it answers one question — do these two strings name the
same person — and leaves the surrounding decision to you.

> **Status: alpha (0.1.0). Partly reviewed — check which part you depend on.**
>
> | Data | Rows | Review status |
> |---|---|---|
> | Name lexicon (`lexicon.tsv`) | 605 | **100% reviewed** by a Yoruba/Igbo speaker |
> | Affix inventory (`elements.tsv`) | 23 | **unreviewed** |
>
> The affix inventory drives candidate generation and has **not** been
> validated by native speakers, though four of its rules were confirmed
> separately (see [Design decisions](#design-decisions), D9). Treat this as a
> recall-improving signal to combine with other evidence, not as a standalone
> identity decision about a real person. See
> [Reviewing the inventories](#reviewing-the-inventories).

## The problem

General-purpose phonetic algorithms encode names by sound, but they were
built for other languages and they make two specific mistakes on Nigerian
names.

**1. They strip affixes in one direction only.** The conventional approach
removes a known leading element and commits to what is left. That works for
the Yoruba pattern, where the short form is a *suffix* of the full name:

```
Adebayo  ->  Bayo          drop the head
```

and it is exactly backwards for the Igbo pattern, where the short form is a
*prefix*:

```
Ifeanyichukwu  ->  Ifeanyi  drop the tail
```

Names carrying elements at both ends fail worst. `Ifeoluwa` is commonly
shortened to `Ife`, but a leading-strip removes `IFE` and keeps `OLUWA` —
discarding the part people actually use and retaining a theophoric element
shared by thousands of unrelated people.

**2. Double Metaphone splits the Igbo `ch` onset.** Measured:

```
DM("CHIAMAKA") -> "KMK"     Italian/Greek CHI -> K rule fires
DM("CHIOMA")   -> "XM"      default CH -> X
```

Same onset, two different codes. Igbo `ch` is a stable affricate and must
never split. This library rewrites `ch` before encoding so it does not.

## Approach

Rather than guess which affix is droppable, `morphex` generates the
**set** of plausible surface forms and matches on set intersection. The full
form is always retained, so precision cannot collapse onto the residues.

```
Ifeoluwa  ->  {IFEOLUWA, IFE, OLUWA}
Ife       ->  {IFE}
                      ^ intersection is non-empty -> match
```

## Install

```bash
pip install morphex
```

## Use

```python
from morphex import match, codes, normalize, explain

match("Ifeoluwa", "Ife")                 # True
match("Ifeanyichukwu", "Ifeanyi")        # True
match("Adebayo", "Bayo")                 # True
match("Muhammad", "Mohammed")            # True
match("Adebayo", "Adewale")              # False

normalize("Dr. Olúwáṣeun")               # 'OLUWASEUN'   folds diacritics, drops titles
codes("Ifeoluwa")                        # {'AFL', 'AF', 'AL'}
```

`match()` is deliberately **recall-oriented**. It is a signal to combine with
other evidence — a date of birth, an account number, a location — not a
standalone identity decision. Names are not unique, and using this alone to
merge records will produce false links regardless of how good the matching is.

`explain()` returns the full derivation, for reviewer-facing tooling:

```python
explain("Ifeanyichukwu", "Ifeanyi")["shared_codes"]
```

## Scope, and what this does not do

- **Hausa is a different problem.** Hausa names are largely Arabic-derived,
  so the dominant failure mode is transliteration variance
  (`Muhammad` / `Mohammed` / `Muhammadu`), not affix dropping. That is
  handled by an explicit variant table, not by candidate generation.
- **Tone marks are folded away.** Yoruba tone and Igbo sub-dots carry real
  linguistic information, but most systems record them inconsistently or not
  at all. Folding is lossy and deliberate.
- **This is not a general African name library.** It covers three Nigerian
  traditions. Other languages need their own inventories.

## Reviewing the inventories

The linguistic rules are **data, not code**. They live in TSV files under
[`src/morphex/data/`](https://github.com/UPSD1/morphex/tree/main/src/morphex/data) so that a speaker can review
them without reading Python:

| File | What it holds |
|---|---|
| `elements.tsv` | Name elements, their tradition, and whether they appear leading, trailing, or both |
| `lexicon.tsv` | Attested Nigerian name forms, used to tell a real residue from a chimera |
| `titles.tsv` | Honorifics that get typed into name fields (`Alhaji`, `Chief`, `Dr`) |
| `hausa_variants.tsv` | Transliteration equivalence groups, pipe-separated |
| `arabic_adaptations.tsv` | Arabic roots as reshaped by different traditions, pipe-separated |

Every row carries a `status` column. Reviewing a row means confirming the
entry and its fields, then setting `status` to `reviewed` and adding your name
to `reviewer`.

| `status` | Meaning |
|---|---|
| `unreviewed` | Assembled from common naming patterns, **not** validated by a native speaker |
| `reviewed` | Confirmed correct by the named reviewer |
| `rejected` | The reviewer confirmed this is **not** a form in use; excluded from attestation |

Rejected rows are kept rather than deleted, so the reasoning survives and
nobody re-adds them later. The first is `MIDE`: `Ayomide` shortens to the head
`Ayo`, not the tail `Mide`.

### `elements.tsv` — what `position` means

| `position` | Meaning |
|---|---|
| `leading` | Element is at the START and the short form drops it — the Yoruba pattern, `Adebayo` → `Bayo` |
| `trailing` | Element is at the END and the short form drops it — the Igbo pattern, `Ifeanyichukwu` → `Ifeanyi` |
| `both` | Attested in both positions |

### `lexicon.tsv` — attested forms

Candidate generation produces residues and some of them are not names.
`ADEBAYO` legitimately yields `BAYO`; it also yields `ADEB`, a bad morpheme
split nobody is called. Structure alone cannot separate them — `YOMIDE` and
`LOLUWA` are perfectly well-formed and still not names. This list can.

It is **advisory, not a filter**, unless you ask for one. Every candidate is
still emitted by default, because the list is incomplete and dropping
unattested forms would silently lose real names. `attested_only=True` trades
recall for precision.

`provenance` is either `generator-pool` (curated Nigerian name lists) or
`common-usage` (widely used given names and short forms).

**Nothing here comes from real records**, and nothing ever should — see D6
under [Design decisions](#design-decisions).

### `arabic_adaptations.tsv` — why it is separate from `hausa_variants.tsv`

`hausa_variants.tsv` holds transliteration spread *within* one tradition:
`MUHAMMAD`, `MOHAMMED` and `MUHAMMED` are one name spelled differently.

This file holds something harder — the same Arabic root absorbed into
different Nigerian languages and reshaped, until no phonetic encoder can
connect the surface forms. `IBRAHIM` and `BURAIMOH` share almost no consonant
skeleton. Only a table links them.

It ships with **one confirmed chain and no guesses**, deliberately. A wrong
adaptation links two different people, and unlike an affix rule there is no
structure to sanity-check it against. Additions want a speaker, not inference.

**The lexicon is where contributions help most.** Every name added closes part
of the coverage gap. Adding a name you know is real is a two-word change with
a measurable effect.

Never add names harvested from real records of any kind. The file is public and
a person's name is personal data even on its own. Names belong here because
they are part of the language, not because someone is called them.

Contributions of this kind are the single most valuable thing anyone can
add to this project. If you speak Yoruba, Igbo or Hausa and you can confirm
or correct even a handful of rows, please open a pull request or an issue.

Adding a row widens recall and costs little precision, since the full form is
always retained. Removing a wrong row is cheap. The risk is not in getting a
row wrong; it is in nobody ever checking.

## Testing

The behavioural contract is a golden corpus at
[`tests/data/golden_pairs.tsv`](https://github.com/UPSD1/morphex/blob/main/tests/data/golden_pairs.tsv) — name pairs
that must match and near-misses that must not. Any change that flips a row
is a breaking change.

```bash
pip install -e ".[dev]"
pytest
```

Note that a passing test on an `unreviewed` row proves only that the code is
self-consistent. It is not linguistic validation.

## Measured effect

Two things matter for a name matcher and they pull against each other: how many
genuine variants it recovers, and how often it collapses two different people
onto the same code.

### Reproducible: the shipped golden corpus

[`tests/data/golden_pairs.tsv`](https://github.com/UPSD1/morphex/blob/main/tests/data/golden_pairs.tsv)
ships with the package — 25 pairs that must match and 10 near-misses that must
not. You can rerun this yourself:

| Configuration | Variant recall | Near-misses kept apart |
|---|---|---|
| default | 24/25 | 10/10 |
| `include_bare_elements=True` | **25/25** | 10/10 |

The single default miss is `Chidera ~ Chi`, which needs bare elements enabled
because `CHI` is an element in its own right.

### Not reproducible: comparison against other encoders

The comparison below was measured against 122 distinct real Nigerian names
that **cannot be shipped** — they are next-of-kin fields from a hospital
record set. You cannot rerun it, so weigh it accordingly.

| Encoder | Variant recall | Collision rate |
|---|---|---|
| Soundex | 4/22 | 24% |
| Double Metaphone | 4/22 | 10% |
| Jaro-Winkler @ 0.92 (JeMPI's default) | 4/22 | 10% |
| `morphex` | 22/22 | 25% |
| `morphex` + lexicon | 22/22 | **11%** |

Three unrelated methods — one phonetic, one older phonetic, one
string-similarity — all score **4/22**. That is the central finding: the gap is
not in the phonetic algorithm, it is the missing morphology layer. Swapping one
encoder for another does not help, because none of them knows that
`Ifeanyichukwu` and `Ifeanyi` are the same person.

Lowering the Jaro-Winkler threshold does not recover it either. At 0.75 recall
reaches only 17/22 while 64% of distinct names get joined to some other name.
The leading-drop cases are unreachable at any threshold — `Chioma ~ Oma` scores
0.00 — because Jaro-Winkler weights the common prefix and leading-drop removes
exactly that.

Generating candidates costs precision: `morphex`'s collision rate lands near
Soundex's, 2.5x Double Metaphone's. The lexicon removes that cost, returning
collisions to Double Metaphone's level while keeping the recall.

**These denominators differ from the corpus above** (22 vs 25) because the
corpus has grown since that comparison was run. Re-running it needs the private
sample, so the older figures are reported as measured rather than silently
rescaled.

### The lexicon

Candidate generation produces residues, and some of them are not names.
`ADEBAYO` legitimately yields `BAYO`; it also yields `ADEB`, a bad morpheme
split. Structure cannot separate them — `YOMIDE` and `LOLUWA` are perfectly
well-formed and still not names anyone has. A lexicon can.

```python
codes("Adebayo", attested_only=True)   # drops ADEB, keeps ADEBAYO and BAYO
is_attested("BAYO")                    # True
is_attested("ADEB")                    # False
```

It is **advisory by default**. The list is incomplete, so absence is weak
evidence: an unattested form may be a real name nobody has recorded yet.
Pass `attested_only=True` to turn it into a filter.

Rows carry `provenance` and `status`. A reviewer who confirms a form is *not*
in use marks it `rejected` and it stops counting as attested — the first such
row is `MIDE`, because `Ayomide` shortens to `Ayo`, not to `Mide`.

**Read the recall figure with care.** The lexicon holds **605 names, all
reviewed**, but it is still far from covering Nigerian naming as a whole, and
the recall figure was reached partly by adding the specific forms the golden
corpus needed. It is therefore tuned to its own test set and should not be read
as generalization. The collision figure is not tuned and is the more
trustworthy of the two.

What the lexicon genuinely does is convert a precision problem into a coverage
problem — and coverage is the kind of problem that gets better when people
contribute.

Hausa is thinnest by some distance and needs a different source before it is
usable; the public name lists that seeded the rest yielded only a few dozen
Hausa entries.

### Which rule earns what

Every rule is individually toggleable, and here is what each one buys and costs:

| Rules enabled | Variant recall | Collision rate |
|---|---|---|
| none (plain Double Metaphone) | 4/22 | 10% |
| `LEADING` | 10/22 | 18% |
| `+ TRAILING` | 19/22 | 20% |
| `+ LINKER` | 20/22 | 20% |
| `+ TRANSLIT` | 20/22 | 20% |
| `+ ELISION` (default) | 22/22 | 25% |
| `+ include_bare_elements` | 22/22 | 45% |
| `+ attested_only` (lexicon filter) | 22/22 | **11%** |

`TRAILING` is the single biggest win: it nearly doubles recall for two points of
collision rate. It is also the rule no general-purpose library has, because it
encodes the Igbo pattern rather than the European one.

`LINKER` and `TRANSLIT` are free. `ELISION` is the marginal call, +2 pairs for
+5 points. `include_bare_elements` is expensive and off by default.

Tune it for your data:

```python
from morphex import candidates
from morphex.candidates import DEFAULT_RULES, ELISION

candidates("Adebayo", rules=DEFAULT_RULES - {ELISION})
```

### In a record-linkage pipeline

As the phonetic component of a linkage token on a 595-record synthetic Nigerian
fixture with 87 known match pairs:

| Implementation | Precision | Recall |
|---|---|---|
| Conventional single leading-affix strip | 100.0% | 33.3% |
| `morphex` | 100.0% | **60.9%** |
| `morphex` (`include_bare_elements=True`) | 100.0% | **63.2%** |

By pattern: Igbo trailing-drop **0% -> 76%**, Yoruba vowel elision 12% -> 100%,
Hausa transliteration 64% -> 82%, and no regression on the Yoruba leading-drop
pattern the conventional approach was built for.

A caution on how this was measured: an earlier version of that fixture generated
its name variants by leading-strip only, so it could not express the Igbo or
Hausa patterns at all, and the measured gain was just +4 points. The fixture had
the same blind spot as the code under test. Treat any name-matching benchmark
with suspicion until you have checked what transformations its test data can
actually express.

Independent evaluation on other real Nigerian name data is wanted and not yet
done. The 122 real names above come from a single source
whose population is 87% Yoruba, so they are directional, not representative.

## Design decisions

The reasoning behind the parts that are easy to get wrong.

**D1. Generate candidates; do not commit to one guess.** Conventional tools
strip one leading affix and keep the residue. Emitting the set and matching on
intersection avoids picking, and the full form is always kept so precision
cannot collapse onto the residues.

**D2. Position is a property of the element, not the tradition.** The first
framing was "Yoruba drops the head, Igbo drops the tail." Real data refuted it:
`OLA` fired trailing 6 times and `AYO` 3 times in a real Nigerian sample.
Yoruba names shorten from the back too. Each element carries its own
`leading` / `trailing` / `both` marking.

**D5. Rejected rows are recorded, not deleted.** When a reviewer confirms a
form is not in use it is marked `rejected` rather than removed. Keeping the row
preserves the reasoning; deleting it invites someone to re-add it later.

**D6. No names from patient records, ever.** The lexicon is public; health data
is not, and a person's name is personal data on its own. The lexicon is built
from curated public name lists and common usage only. Real records are used to
*measure* this library, never to populate it.

**D7. Preprocess `CH` before Double Metaphone.** Bare Double Metaphone splits
the Igbo `ch` onset because its Italian/Greek `CHI` → K rule fires on some
names and not others. Rewriting `ch` → `tch` forces the default branch and
makes the onset consistent.

**D8. Generation is shallow.** Each candidate is at most one rule from the
original and derived forms are never re-derived from. Chaining produced
chimeras: `ADEBAYO` → `ADEB` (bad split) → `DEB` (elision on the bad split).
The longest element also wins, so `OLUWASEUN` strips `OLUWA`, not `OLU`.

**D9. Yoruba names shorten to the head, not the tail.** Confirmed by
native-speaker review. People are called `ADE` from `ADEIFE`, `AYO` from
`AYOOLA`, `IFE` from `IFEOLUWA` — never the tail. The suppression fires only
when the tail is itself a known element, so ordinary name parts survive
(`ADETOKUNBO` → `TOKUNBO` is correct as it stands). Scoped to Yoruba
deliberately: Igbo behaves differently, where `OBI` is both an element and a
genuine short form of `OBINNA`.

**D11. Arabic-derived names cross traditions and get reshaped.** The same root
is absorbed into different languages and comes out phonologically altered:
Hebrew *Avraham* → Arabic *Ibrahim* → Yoruba *Buraimoh*. `IBRAHIM` encodes to
`APRHM` and `BURAIMOH` to `PRM` — no shared code, and Jaro-Winkler scores them
near zero. Nothing structural links these; only a table does. It ships with one
chain and no guesses, because a wrong adaptation links two different people and
there is no structure to sanity-check it against.

## Known limitations

1. **The affix inventory is unreviewed.** 23 elements, none validated by a
   native speaker.
2. **`ELISION` over-fires.** It generates forms that are not used in practice
   (`OLUWASEUN` → `LUWASEUN`). Defining when it should apply needs a speaker.
3. **Real-name evaluation is from a single source** whose population is
   roughly 87% Yoruba. Directional, not representative. Independent evaluation
   on other Nigerian name data is wanted and not yet done.
4. **Only three traditions are covered.** The same sample contained Igede,
   Anang, Ijaw, Itsekiri and Igala names. Nothing here handles them.

## Versions

**0.1.0** — first release. Affix-aware candidate generation for the Yoruba
leading-drop and Igbo trailing-drop patterns, linking-consonant shedding,
initial-vowel elision, Hausa transliteration groups, and the Arabic adaptation
table. Igbo `ch` onset stabilized. 605-name reviewed lexicon with
`attested_only` filtering. Individually toggleable rules with a published
ablation. `explain()` for reviewer-facing traces.

Any change that flips a row in the golden corpus is a breaking change and
requires a major version bump once 1.0.0 is reached.

## License

MIT — see [LICENSE](https://github.com/UPSD1/morphex/blob/main/LICENSE).
