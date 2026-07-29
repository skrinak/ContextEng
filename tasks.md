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
- [ ] Re-vendor `CLAUDE.md` into groundwork and confirm `contract-sync` green `[pending]`

## Open

- [ ] `vision/` — not created. Nothing here is aspirational positioning yet, and an empty directory is a claim that isn't true `[pending]`
