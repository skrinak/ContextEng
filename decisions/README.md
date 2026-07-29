# `decisions/` — one-time records, frozen once terminal

> **Membership test**
> "This records a moment. If you'd edit the body to reflect today's system, it doesn't belong here."

The default home for a new markdown file: born here with `> **Status:** Proposed` unless it passes
another bucket's test on day one.

Every record's first line after the H1 is its status — CI fails without it:

| Status | Frozen? |
|---|---|
| `Proposed` · `In-progress` | No — live, edit freely |
| `Shipped (YYYY-MM-DD)` · `Superseded-by: <path>` | **Yes** — append a status line, never rewrite the body |

Generated output goes to `evals/`, never over a curated record.

Full conventions and the freeze rule: https://github.com/skrinak/groundwork/blob/main/decisions/README.md
