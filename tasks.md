# tasks.md

In-flight work on the method itself. One of the three root files, because it answers "what is
happening right now?" without being asked.

## Conventions

Detail lives in `decisions/`; status lives here. Mark user-owned items explicitly. Archive completed
workstreams into `decisions/` at boundaries.

---

## Conform ContextEng to the taxonomy (2026-07-29)

Tracking `decisions/2026-07-29 - Conform ContextEng to the groundwork archetype.md`.

- [x] Install the reference guard + fixture suite + CI `[completed]` — green before the moves, so the restructure was verified rather than trusted
- [x] `docs/UV Setup.md` → `runbooks/` `[completed]` — a step-by-step operator procedure, misfiled since it was written
- [x] `prompts/` → `specs/` `[completed]` — machine-fetched text whose paths are API; the guard caught all 10 stale references
- [x] Bucket READMEs in every directory `[completed]` — membership test verbatim, pointing at the archetype for the canonical text
- [x] `CLAUDE.md` gains "The tree" as a first-class section `[completed]` — placement procedure, per-bucket permissions, source precedence, post-`/clear` reading order
- [x] Re-vendor `CLAUDE.md` into groundwork and confirm `contract-sync` green `[completed]` — verified 2026-09-03: CLAUDE.md/settings.json/env.example byte-identical, last 10 daily runs green

## Replace FSIregulation.md with a validated corpus (2026-09-17)

Tracking `decisions/2026-09-17 - Replacing FSIregulation.md with a validated corpus.md`.

- [x] Survey the replacement, its taxonomy placement and its inbound references `[completed]` — found two demonstrable defects in the current file (duplicate citation URL, authority/host mismatch) and one legislative-status error
- [x] Fix the defects the survey found `[completed]` — each Act points at its own subchapter; MSRB points at msrb.org; HIPAA, NIST, GDPR and AML moved out of "Global"; GENIUS Act added, and the 2022–23 stablecoin bills marked not enacted. Also found and fixed: 17 dead links and a withdrawn SEC proposal presented as law
- [x] Where generated machine-consumable JSON lives `[completed]` — the record's recommendation, at `specs/fsi/export/` (`dist/` is gitignored repo-wide); exception recorded in `specs/README.md`. **Owner to confirm**
- [x] Toolchain, schemas and validator with a fixture per failure mode `[completed]` — `utils/fsi_corpus.py`, 20 case fixtures, `make fsi-check`, CI `fsi-corpus.yml`
- [x] Seed corpus, Layer 1, seven auditability instruments `[completed]`
- [x] Rendering, export, link verification, coverage report `[completed]` — `docs/FSIregulation.md` generated at the same address, plus `docs/regulations/{us,eu}.md` and `specs/fsi/export/corpus.json`
- [x] Obligations for the seven, every source fetched and every duration quoted `[completed]` — 34 obligations; quotes compared verbatim against source text retrieved 2026-09-18
- [x] Controls and AWS bindings `[completed]` — 11 controls; every obligation has at least one
- [x] Re-vendor `CLAUDE.md` after its FSI bullet repoints `[completed]` — not needed, because the address did not move
- [ ] **User-owned:** human/counsel review of the 34 obligations before relying on them `[pending]`
- [ ] Flip the decision record to `Shipped` once this work is merged `[pending]`
- [ ] Next cluster: model risk and AI governance, then operational resilience and third-party risk, UK, EU core `[pending]`

## Open

- [ ] `vision/` — not created. Nothing here is aspirational positioning yet, and an empty directory is a claim that isn't true `[pending]`
