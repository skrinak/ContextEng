# `specs/` — machine-parsed. The path is API.

> **Membership test**
> "Code, tests, or an external tool **parses** this — the path itself is API."

The prompts live here because that is what they are: text a machine fetches and parses. The
TaskListGenerator's Output Format section *is* the parsing contract downstream tools validate
against. Their raw URLs are hardcoded across other repositories and baked into already-seeded
customer repos, so **moving a file here is a breaking change in someone else's repository.**

| File | Consumed by |
|---|---|
| `PRD_DevelopmentPrompt.md` | Humans and agents starting a PRD |
| `TaskListGenerator.md` | Pointer — the payload stays at `../docs/TaskListGenerator.md` |
| `Code-Reviewer.md` | Fetched by raw URL on a review cadence |

## The documented exception

**`docs/TaskListGenerator.md` holds the payload, not this directory.** That URL is hardcoded in 9
files of one downstream repo alone, plus seeded customer repositories we cannot reach. Automation
that curls it receives HTTP 200 whatever sits there, so a pointer at that address **fails silently** —
the consumer gets a redirect note instead of a spec with no error to notice. Taxonomically it belongs
here; the public-API constraint outranks tidiness, and this paragraph is the record of that trade.

Before moving anything in this directory: grep every repo, check every raw URL, and remember that a
200-returning stub does not preserve a machine-facing contract.

Archetype: https://github.com/skrinak/groundwork
