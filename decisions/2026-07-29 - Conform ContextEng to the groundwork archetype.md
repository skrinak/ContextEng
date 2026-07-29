# Conform ContextEng to the groundwork archetype

> **Status:** Shipped (2026-07-29)
> **Pairs-with:** [`../docs/REPOSITORY_TAXONOMY.md`](../docs/REPOSITORY_TAXONOMY.md)

## Context

ContextEng defined the taxonomy and did not follow it. That was justified at the time on the grounds
that ContextEng is a prompt library rather than a product, so its four-bucket shape was "the method
working, not an inconsistency" — a position written into `REPOSITORY_TAXONOMY.md` §10.

Two things made that position untenable within a week of writing it.

**The exception was doing real damage.** `CLAUDE.md` is fetched and seeded verbatim into every
project built with this method, and it linked its own `docs/` *relatively*. Those links resolved
here and were dead in every seeded repository — for roughly a year. The defect was **invisible from
inside ContextEng**, because here the paths resolve. It surfaced only when a separate scaffold
repository ran the reference guard against a copy. A repo that exempts itself from its own rules
cannot check itself, and what it cannot check, it gets wrong.

**The audit did not survive contact.** Applied honestly, the placement procedure immediately found
`docs/UV Setup.md` misfiled — a step-by-step operator procedure sitting in the documentation bucket
since it was written. The four-bucket shape had not been a considered classification; it was the
absence of one.

## Decision

**[skrinak/groundwork](https://github.com/skrinak/groundwork) is the archetype.** ContextEng conforms
to it rather than justifying an exception.

- Installed the reference guard, its fixture suite and CI — **before** moving anything, so the
  restructure was verified rather than trusted. It caught all 10 stale references the moves created.
- `docs/UV Setup.md` → `runbooks/`. A procedure, executed again.
- `prompts/` → `specs/`. Machine-fetched text whose paths are API. The Output Format section of the
  TaskListGenerator *is* a parsing contract downstream tools validate against, which is the `specs/`
  membership test almost word for word.
- A `README.md` in every directory carrying its membership test verbatim.
- `CLAUDE.md` gains **The tree** as a first-class section — placement procedure, per-bucket
  permissions, source precedence, post-`/clear` reading order — written for an agent to execute.
- `tasks.md` added; root is now the full trio.

## The exception that remains, deliberately

**`docs/TaskListGenerator.md` keeps the payload** though it is taxonomically a spec. That raw URL is
hardcoded in 9 files of one downstream repo alone plus seeded customer repositories we cannot reach,
and automation curling it receives HTTP 200 whatever sits there — so a pointer at that address fails
*silently*. The public-API constraint outranks tidiness. Recorded in `specs/README.md` rather than
left as a puzzle.

`vision/` was not created. Nothing here is aspirational positioning, and an empty directory is a
claim about the repository that isn't true yet.

## Consequences

- ContextEng can now be checked by the guard it ships. The class of defect that hid for a year is
  mechanically detectable here.
- `REPOSITORY_TAXONOMY.md` §10 needed rewriting: it argued for copying the axis rather than the
  buckets, using ContextEng's exception as the worked example. The axis point stands; the example was
  wrong and is replaced by the real constraint — public-API paths — which is a far better teacher.
- Anyone who bookmarked `prompts/*` raw URLs must repoint to `specs/*`. Those URLs were three hours
  old; the machine-consumed one at `docs/TaskListGenerator.md` is untouched.
- Repos seeded before today carry a `CLAUDE.md` with relative doc links. Re-vendor to fix.
