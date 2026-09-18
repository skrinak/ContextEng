# `specs/fsi/` — the FSI regulatory corpus

The source of record for [`docs/FSIregulation.md`](../../docs/FSIregulation.md) and
[`docs/regulations/`](../../docs/regulations/). Those files are generated from this directory. Edit here,
then run `make fsi-render`.

| Path | Layer | Holds |
|---|---|---|
| `registry.yaml` | — | Jurisdictions, authorities and vendors, and the hosts each may be cited from |
| `instruments/<id>.yaml` | 1 | What the law is: citation, authority, jurisdiction, status and when it was established |
| `obligations/<instrument>.yaml` | 2 | What a firm must evidence: ISO 8601 durations, triggers, and a verbatim quote of the primary source |
| `controls/<id>.yaml` | 3 | How obligations are implemented and proved, with AWS bindings |
| `holding.yaml` | — | References carried over from the old link list and not yet migrated. They assert nothing beyond their link |
| `schema/*.schema.json` | — | JSON Schema (2020-12) for each record type |
| `export/corpus.json` | — | **Generated.** Every layer joined, plus coverage. Consumers fetch it by address |

Rules the validator enforces, each backed by a fixture in `utils/tests/fixtures/fsi/cases/`:

- Every number in a retention period or a requirement appears in the quoted source.
- Every instrument carries at least one obligation, and obligations come only from law in force.
- Every cited host belongs to the named authority or to an official publisher in its jurisdiction.
- A record's jurisdiction matches its authority's.
- No two entries share an address.
- Bills and proposals state whether they became law.
- Every record has a review date at most a year after it was verified. Once that date passes, the build fails.

`high` confidence means the current primary text was read and compared against. Do not raise a record to
`high` without doing that. When adding an instrument, move its entry out of `holding.yaml` in the same
change.
