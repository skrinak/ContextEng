# Moved

The peer code-review prompt lives at [`../specs/Code-Reviewer.md`](../specs/Code-Reviewer.md).

Note the filename also changed: the space became a hyphen (`Code Reviewer.md` → `Code-Reviewer.md`),
so a URL that percent-encoded the space (`Code%20Reviewer.md`) will not find it under its new name
either.

This stub exists because the 2026-07 prompts/docs split moved the file without leaving one, and the
prompt is fetched by raw URL on a review cadence — a bookmark or script pointing at
`https://raw.githubusercontent.com/skrinak/ContextEng/refs/heads/main/docs/Code%20Reviewer.md`
got a 404 with no hint of where it went (xact.ai `decisions/2026-07-28 - Code Review.md`, F10).

Unlike its sibling `TaskListGenerator.md` — whose payload had to move *back* to `docs/` because
automation consumes it and a 200-with-a-pointer fails silently — this one is fetched by humans, who
read a 404 and then read this page. A pointer is the right shape here; a stub that lies is not.
