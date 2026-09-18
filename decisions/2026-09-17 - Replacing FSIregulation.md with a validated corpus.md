# Replacing FSIregulation.md with a validated corpus

> **Status:** In-progress
> **Pairs-with:** [`../docs/FSIregulation.md`](../docs/FSIregulation.md)

## Context

[`docs/FSIregulation.md`](../docs/FSIregulation.md) is 116 lines of categorised hyperlinks: three
geographic headings, sub-category sub-headings, 76 links, no source of record behind it. It is
filed in the bucket table as "Reference guidance" and it is the artifact `CLAUDE.md` points an agent
at when a workload is regulated.

The form has predictable failure modes, and this file has every one of them. Two are already present and
mechanically demonstrable rather than hypothetical:

- The Investment Company Act and the Investment Advisers Act entries resolve to the **same URL**
  (`USCODE-2019-title15-chap2D.pdf`). One of the two is wrong, and nothing in the repository can tell
  which.
- The MSRB Rules entry links to a `finra.org` address. The named authority and the host disagree.

A third is structural: HIPAA and NIST sit under a "Global" heading while both are US instruments, and
GDPR sits there while it is EU. That destroys the only query anyone runs against this file, which is
"what applies to us in jurisdiction X".

The fourth is the dangerous one. The Stablecoins subsection presents 2022 and 2023 bills as the state
of the law. US federal stablecoin law was enacted in 2025. Nothing in the file carries a status or a
date, so the staleness is invisible, and a model reading it inherits the error with no signal.

The fifth is the one that makes the file useless rather than merely wrong: **it contains citations and
zero obligations.** A link to Regulation E does not encode the error resolution clock. A link to Rule
17a-4 does not state a retention period. The file names the law and omits the requirement, which is
the only part a reader needed. Its own title promises "auditability requirements" and it contains none.

None of this is checkable. A flat link list has no schema, so every defect above stays invisible until
somebody happens to notice, which is the same class of failure the reference guard was built to end.

## What replacement requires

A three-layer dataset with a validator, not a better-organised list. Instruments (what the law is),
obligations (what a firm must evidence, with ISO 8601 durations and a mandatory quoted source for any
number), controls (how it is implemented and proved). The full build specification runs to about 1,280
lines and 114 numbered requirements; it is not reproduced here.

Six things in this repository have to change, and they are the actual cost.

**1. Taxonomy placement. The build spec's layout is illegal here.** It proposes top-level `data/`,
`scripts/` and `dist/`. `CLAUDE.md` forbids new top-level buckets outright, and each of those three
already has a home under the placement procedure:

```
specs/fsi/                     corpus YAML + JSON Schemas — a machine parses it, the path is API
specs/fsi-corpus-build.md      the build spec itself, parsed by the agent executing it
utils/fsi_*.py                 validator, renderer, exporter, link checker, coverage
utils/tests/test_fsi_*.py      their fixture suite
docs/FSIregulation.md          GENERATED index, same address it has today
docs/regulations/<juris>.md    GENERATED per-jurisdiction pages
```

**One placement question is genuinely open and is the repo owner's call:** where the generated
machine-consumable JSON goes. `decisions/evals/` is the stated home for script output, but that
convention assumes dated one-off records, and these artifacts must live at a *stable* path because an
agent fetches them by address. `specs/fsi/dist/` satisfies the `specs/` membership test exactly and
breaks the cleaner rule that generated and curated content do not share a bucket. Recommendation:
`specs/fsi/dist/`, with the generated-file banner and a line in `specs/README.md` recording the trade,
matching how the `TaskListGenerator.md` exception is handled today.

**2. Three inbound references, one with downstream blast radius.**

| Reference | Note |
|---|---|
| `README.md:122` | Relative link in the docs listing. Trivial. |
| `docs/README.md:15` | Bucket table row, currently pairs it with `FEDERATED_SSO.md` as "Reference guidance". Needs its own row: it stops being a link list. |
| `CLAUDE.md:132` | The FSI constraints bullet. **`CLAUDE.md` is vendored byte-identical into groundwork and seeded into every project built with this method.** Editing this line means re-vendoring and confirming `contract-sync` green, exactly as the 2026-07-29 conformance work did. |

**3. The public address must not move.** The blob and raw URLs for `docs/FSIregulation.md` are public,
and this file was fetched by raw URL during the work that produced this record, so at least one
consumer pattern exists. `specs/README.md` already records what happens at an address automation
curls: it returns HTTP 200 for whatever sits there, so a pointer or a stub **fails silently**. The
replacement therefore keeps the path and changes the contents. Replace means regenerate in place.

**4. The validator ships with tests or it does not ship.** `utils/README.md` and the guard's own
docstring make this repository's position unambiguous: the checker `check_doc_links.py` replaced had no
tests and reported "OK" straight through a restructure that broke roughly 282 references. A corpus
validator without a fixture per rule would repeat that failure with higher stakes, because the output
is regulatory assertions. Every failure-mode detector needs a fixture that fails before it is
implemented and passes after.

**5. Toolchain must follow house convention.** `uv run --no-project`, never bare `python` or `pip`.
New `Makefile` targets in the existing style, `.PHONY` with a rationale comment. A CI workflow
alongside `docs-links.yml`. The reference guard checks paths in non-markdown files too, so corpus YAML
carrying repo-relative paths is in scope for it, with `doclink: ignore` as the escape.

**6. Content parity is a trap, and this is the finding worth arguing about.** The 76 existing links
lift to instrument records mechanically, in an afternoon. But an honest migration cannot mark them
`confidence: high`, because that level means the primary source was actually read, and reading 76
primary sources is the entire cost of this project. A faithful lift therefore produces a corpus that is
*visibly* mostly low-confidence, which reads as a regression to anyone who liked the old file's
unearned authority. That reaction should be expected and refused: the confidence levels are the
improvement, not a defect in it.

## Recommended scope

Do not migrate all 76 links in one pass. Ship the machinery, then one verified cluster:

1. Toolchain, taxonomy, schemas, validator with fixtures. No corpus data. Proves the failure modes are
   detectable before anything can exhibit them.
2. Seed corpus, Layer 1 only, seven instruments: SEC 17a-3, 17a-4, 204-2, FINRA 4511, CFTC 1.31,
   MiFID II Article 16(6), SOX 802.
3. Rendering, export, link verification, coverage report.
4. Obligations for those seven, every source fetched, every duration quoted. This is the cluster where
   a link list is most obviously inadequate, so it demonstrates the point immediately.
5. Controls and AWS bindings for those obligations.

The remaining links stay reachable throughout, rendered into a clearly labelled unmigrated appendix
from a holding record, so no information is lost and none of it is overstated. Expansion after that is
one cluster per change, highest architectural impact first: model risk and AI governance, then
operational resilience and third-party risk, then the UK, then EU core regimes.

## Consequences

- `docs/FSIregulation.md` becomes generated and stops being hand-editable. The bucket table needs to
  say so, and the pre-commit hook and CI need to enforce it.
- The corpus can answer questions the file cannot, which is the point: retention periods sorted by
  duration, obligations with sub-72-hour notification deadlines, what applies in the EU to a bank at
  high cloud relevance. Those are `jq` queries against a build artifact, not prose retrieval.
- Regulatory assertions acquire provenance and an expiry. Records carry `review_due`, and a stale
  record fails the build rather than quietly misinforming a reader. This is a standing maintenance
  obligation the current file does not impose, and accepting it is part of accepting this proposal.
- Absence of regulation becomes representable, distinct from absence of coverage. That matters most
  for crypto, where several areas have no applicable standard at all: institutional key management,
  proof-of-reserves attestation, the DeFi authorization perimeter, and autonomous agents transacting
  on-chain. A reader currently cannot tell those apart from topics nobody got round to.
- As surveyed, nothing above was implemented. See Outcome for what was built, and the placement question in item 1 wanted
  an answer before the first line of code.

## Outcome (2026-09-18)

Recommended scope items 1 to 5 are implemented. The survey's counts were corrected in place while this
record was still open: the file held 76 links, not roughly 90.

- **Placement question answered.** The recommendation was adopted, at `specs/fsi/export/` rather than
  `specs/fsi/dist/`, because `dist/` is ignored repo-wide. The trade is recorded in `specs/README.md` as
  its second documented exception.
- **The corpus.** Seven instruments (SEC 17a-3, 17a-4 and 204-2, FINRA 4511, CFTC 1.31, MiFID II
  Art 16(6), SOX 802), 34 obligations and 11 controls, all under `specs/fsi/`. Every obligation's quote was
  compared verbatim against text retrieved from eCFR, finra.org, uscode.house.gov and publications.europa.eu.
  All 34 obligations have at least one control. The US records are `high`. The EU records are `medium`: the
  Official Journal originals were read, but EUR-Lex refuses automated retrieval of consolidated text.
- **Two corrections to this record's own findings.** The Investment Company Act / Advisers Act URL was not
  wrong for either Act: chapter 2D of Title 15 contains both. It was imprecise, and each Act now points at its
  own subchapter. Separately, the survey missed a whole defect class: at migration, 13 links returned 404
  (17 counting sec.gov pages that return 404 once a User-Agent is declared). The SEC "custody rule
  amendments" entry was a proposed rule, withdrawn on 2025-06-17. All are corrected in `holding.yaml`, with the
  replaced address kept against each entry. One dead FinCEN link could not be identified and stays recorded as
  dead rather than guessed at.
- **Tooling.** `utils/fsi_corpus.py`, `utils/fsi_render.py` and `utils/fsi_links.py`, with 20 failure-mode
  fixtures in `utils/tests/fixtures/fsi/cases/`. CI runs `make fsi-check` on every push, plus a weekly
  scheduled link check. The first link report is `decisions/evals/2026-09-18-fsi-link-check.md`.
- **`CLAUDE.md` did not need re-vendoring.** Its FSI bullet points at `docs/FSIregulation.md`, and that
  address did not move.
- **Still open.** A human reviewer, ideally counsel, should confirm the obligations before anyone relies on
  them; `verified.by` says so on every record. Quote verification against live sources is not automated: it
  was done once, against text fetched on 2026-09-18. Records that mark a regulatory gap (the Consequences bullet
  on crypto) are not modelled yet. Expansion continues one cluster per change, in the order given above.

