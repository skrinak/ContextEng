# `docs/` — the method, as it is

> **Membership test**
> "This describes the system **as it is** — if the system changes and this file doesn't, that's a bug."

ContextEng's "system" is the method, so this bucket holds the method's current state: the
architecture posture, the taxonomy, the reference guidance. Living — when the method changes, these
change.

| File | |
|---|---|
| `AGENTCORE_FIRST.md` | Architecture, buy-vs-build ledger, migration playbook |
| `REPOSITORY_TAXONOMY.md` | The tree design and its full rationale |
| `WORKFLOW_NARRATIVE.md` | The development workflow in detail |
| `FEDERATED_SSO.md` | Reference guidance |
| `FSIregulation.md` · `regulations/` | **Generated** from `../specs/fsi/` by `make fsi-render`. CI fails if they drift, so edit the corpus rather than these files |
| `TaskListGenerator.md` | **A spec living here by public-API constraint** — see `../specs/README.md` |
| `images/` | Whiteboard boards + their regenerable `.content.txt` sources |

Archetype: https://github.com/skrinak/groundwork/blob/main/docs/README.md
