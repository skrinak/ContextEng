# Moved

The TaskListGenerator prompt lives at [`../docs/TaskListGenerator.md`](../docs/TaskListGenerator.md).

It is the one prompt in this repo that does **not** live under `prompts/`, and that is deliberate.
Its raw URL —

```
https://raw.githubusercontent.com/skrinak/ContextEng/refs/heads/main/docs/TaskListGenerator.md
```

— is public API. It is hardcoded in 9 xact.ai files, cited in frozen decision records, presented
publicly in `README.md` as the spec the generated PRD conforms to, and baked into already-seeded
customer repositories whose owners we cannot reach. Automation curls it for the task-generation
rules and gets a 200 whatever we leave at that address, so a pointer there fails *silently*: the
consumer receives a redirect note instead of a spec, with no error to notice.

The 2026-07 prompts/docs split moved the body here and left a stub at the URL, which broke exactly
that (xact.ai `decisions/2026-07-28 - Code Review.md`, F10). The direction is now inverted — payload
at the public address, pointer here — rather than duplicated, because two copies of a 246-line spec
drift.

**If you are reorganizing this repo:** the payload must stay at `docs/TaskListGenerator.md` until
someone has audited every consumer of that raw URL, including consumers outside this organization.
