# Repository Taxonomy — designing a source tree that an AI can read

> **What this is.** A classification system for the non-code files in a software repository, and
> the reasoning behind it. It answers "where does this file go" with a rule you can apply to a file
> type that does not exist yet, rather than a list you extend every time someone invents an artifact.
>
> **Who it is for.** Teams whose repositories are read by coding agents as well as by people. If no
> model ever reads your tree, most of this still holds — it will just feel like ordinary good
> hygiene. If models do read it, the cost of getting it wrong is different in kind, and §1 is why.

---

## 1. The premise: a directory tree is a context-selection index

The traditional job of a source tree is *retrieval* — help a human find a file. Search solved that
years ago. `grep`, fuzzy-open, and semantic search all find a file by what it is **about**, and they
do it better than a folder hierarchy ever did.

What search does **not** tell you is how to *treat* what you found. Three questions survive retrieval:

| Question | Why a reader cannot answer it from the file's content |
|---|---|
| **Is this true now?** | A design doc and a postmortem are both confident, well-written prose in the present tense. Nothing in the writing distinguishes "this is how the system works" from "this is how we thought it would work, eighteen months ago." |
| **May I change it?** | Some files are the current description of reality and must be updated when reality moves. Others are dated records whose entire value is that they were *not* updated. |
| **Is something parsing this?** | A path that a test fixture, a CI job, or a downstream repo resolves at runtime is API. Moving it breaks things silently, at a distance, in someone else's repository. |

A human resolves these with tribal knowledge — *oh, that folder is where old design docs went to die.*
An agent has no tribal knowledge. It has the path, the filename, and whatever it reads. So in a
repository that agents work in, **the path has to carry the answer**, because the path is the one
piece of metadata that is present in every listing, every search result, every tool output, and every
prompt — for free, before any file is opened.

That reframes the tree. It is not filing. It is a **precomputed retrieval filter**: a way of telling
a reader — human or model — how much authority to grant a document *before* spending tokens on it.

### The failure this prevents

The expensive failure in agentic development is not an agent that cannot find context. It is an agent
that finds the **wrong** context and cannot tell.

A superseded design document is the sharpest example. It is detailed, internally consistent, written
with conviction, and wrong. An agent that loads it as current truth will produce work that is
confidently, coherently wrong — and the coherence is what makes it expensive, because the output
looks *more* trustworthy than a hedged answer would. The agent will cite the document. A reviewer
skimming the citation will nod.

You cannot fix this by writing better documents. The superseded document was a good document. You fix
it by making "superseded" a property of the file's **location and header**, visible before it is read.

> **The one-sentence version.** Classify by *how a reader must treat the file*, never by *what the
> file is about*. Aboutness is what search is for; treatment is what the tree is for.

---

## 2. The classification axis

Every file gets classified on three questions, in this order:

1. **Audience** — who consumes it? A human reading for understanding, a machine parsing a contract, an operator executing a procedure, or the model/harness itself?
2. **Lifecycle** — does it describe the present (and so must change when the system changes), or does it record a moment (and so must *not*)?
3. **Bindingness** — is the path itself load-bearing? Does anything resolve it at runtime?

Three axes, and the buckets fall out. Note what is **not** on the list:

- **Not file extension.** `.md` is not a category. A markdown API contract and a markdown postmortem have nothing in common except their renderer.
- **Not topic.** See §5 — this is the most common mistake and it deserves its own argument.
- **Not authorship.** "Docs the AI wrote" is not a bucket. Provenance goes in a header, not a path.
- **Not recency.** "Archive" is not a lifecycle. A record is frozen the day it is written, not after it gets old.

---

## 3. The buckets

The product-repository shape. Six buckets plus a fixed root.

| Bucket | Membership test — the question that decides | Lifecycle | Typical contents |
|---|---|---|---|
| **root** | "An agent must load this unconditionally, every session, without being asked." | Living | Exactly three: `README.md`, `CLAUDE.md`, `tasks.md` |
| **`docs/`** | "This describes the system **as it is** — if the system changes and this file doesn't, that's a bug." | Living | Architecture, the authoritative system inventory, public API reference, invariant specs |
| **`specs/`** | "Code, tests, or an external tool **parses** this — the path itself is API." | Living, path-frozen | OpenAPI/JSON Schema, contracts validated in CI, machine-read fixtures |
| **`runbooks/`** | "A step-by-step procedure an operator will execute **again**." | Living | Migrations, deploys, rollbacks, test plans, incident procedures |
| **`decisions/`** | "This records a moment. If you'd edit the body to reflect today's system, it doesn't belong here." | **Frozen once terminal** | Design docs, task ledgers, reviews, postmortems, correspondence, spikes, audits |
| **`vision/`** | "This describes the product we **intend**, not the system that exists." | Living | PR-FAQs, positioning, founding notes, strategy |
| **`.claude/`** | "Consumed by the model or the harness, not read by humans for understanding." | Consumable | Skills, slash commands, hooks, settings |

**Why the root is exactly three.** Root is the only location an agent reads without being told to,
so it is the scarcest real estate in the repository and the only place where an unclassified file
costs tokens on *every* session. Three files, three jobs: `README.md` is what this is, `CLAUDE.md` is
how to work here, `tasks.md` is what is in flight. A fourth file at root is nearly always a
`decisions/` record that has not been filed yet.

### Definitions

Terms are used precisely throughout. Where two words are colloquially interchangeable, this taxonomy
picks one meaning and holds it.

| Term | Definition | Not to be confused with |
|---|---|---|
| **Record** | A document about a moment. Its value is that it was true *then*, and it is not maintained. | Documentation, which is about *now* and must be maintained. |
| **Documentation** | A present-tense description of the system as it currently exists. Carries an obligation: when the system changes, this changes. | A design doc — which is a record of what was *planned*, and is frozen the moment it ships. |
| **Spec** | A file whose **path and shape** are consumed by a machine. Moving it is a breaking change even if the content is identical. | Documentation about an interface, which is prose in `docs/`. |
| **Runbook** | An ordered procedure with verifiable steps, intended for repeat execution. | A record of one execution — that is a `decisions/` record. |
| **Vision** | Intent. Deliberately *not* the system; expected to be aspirational. | Documentation, which would be a bug if it were aspirational. |
| **Terminal status** | `Shipped` or `Superseded-by` — the record has reached its final state and is frozen. | `Proposed` / `In-progress`, which are live and editable. |
| **Generated artifact** | Machine-written data (a benchmark scorecard, an eval run). Never hand-edited; re-running writes a *new* dated file. | A record, which is hand-written and carries a status. |

### The status vocabulary

Every `decisions/` record opens with one blockquote line. This is what makes staleness
machine-readable — the single highest-leverage convention in the whole system.

| Status | Meaning | Frozen? |
|---|---|---|
| `> **Status:** Proposed` | Written, not agreed or executed. | No — live, edit freely |
| `> **Status:** In-progress` | Being executed now; a tracker or an open ledger. | No — live, edit freely |
| `> **Status:** Shipped (YYYY-MM-DD)` | Executed. The record now describes history. | **Yes** |
| `> **Status:** Superseded-by: <path>` | A later record replaced it. The pointer is mandatory. | **Yes** |

Paired records (a design and its execution ledger; a review and its fix plan) additionally carry
`> **Pairs-with:** <path>`, so that finding one always finds the other.

---

## 4. Why a code review goes in `decisions/`

This is the question that most sharply separates classification-by-treatment from
classification-by-topic, so it is worth working all the way through rather than asserting.

**What a code review actually is**, as an artifact:

- **Point-in-time.** True as of one commit, one date, one scope.
- **Observational, not descriptive.** It records what was *found*, not what *is*. The instant the first fix lands, its findings are partly obsolete — by design, because fixing them is the point.
- **Never maintained.** Nobody will update a 2026 review to match 2027 code, and nobody should. A re-review produces a *new* record; it does not edit the old one.
- **Consequential.** It drives a fix plan. The pair must remain legible together, years later, to answer "why is the code like this?"

Now test it against every candidate location:

| Candidate | Verdict | Why |
|---|---|---|
| **`docs/`** | ✗ Actively harmful | `docs/`'s contract is *"if the system changes and this file doesn't, that's a bug."* A review violates that from the moment the first fix lands. You then get one of two outcomes, both bad: someone is obligated to maintain a review forever (absurd — it's an observation, not a description), or stale files become normal inside the one bucket whose entire value is being current. The second is worse: it teaches every reader, human and model, that `docs/` cannot be trusted. **One misfiled record devalues the whole bucket.** |
| **`reviews/`** (topic bucket) | ✗ Fails to generalize | It answers "what is this about" — which you already knew from the filename. And it sets a precedent: the next artifact type needs `postmortems/`, then `audits/`, then `spikes/`, then `incidents/`, then `retros/`. Each holds one or two files. None has a rule for where the *next* new type goes, so every new artifact reopens the debate. |
| **`runbooks/`** | ✗ Wrong lifecycle | A runbook is executed *again*. A review is executed once. Re-reviewing writes a new record rather than re-running the old one. |
| **`specs/`** | ✗ Nothing parses it | The path isn't API. No tool resolves it. |
| **root** | ✗ Wrong tier | Root is what an agent loads *unconditionally*. A review is the opposite: read once, deliberately, when you need history. |
| **Issue tracker only** | ✗ Leaves the tree | An agent working in the repository cannot see it. And the "why" evaporates on the next tracker migration — which always comes. |
| **`decisions/`** | ✓ | Its contract is *exactly* "a frozen record of a moment, carrying a status header that tells you whether it still matters." A review is decision-shaped: **we looked, this is what we found, this is what we resolved to do.** |

**The generalization.** `decisions/` is the default home for *any* one-time artifact — which is why
the birth rule (§6) sends new files there unless they clearly pass another bucket's test. The
asymmetry is the point: a one-time record misfiled as living documentation quietly corrupts the
bucket readers trust most, while living documentation misfiled as a record is obvious and harmless —
someone opens it, sees a stale `Shipped` header on a file that clearly describes the present, and
moves it. **Optimize for the cheap mistake.**

---

## 5. Why not topic directories

The most common alternative — `security/`, `qa/`, `cicd/`, `evals/`, `infra/` — fails for four
compounding reasons.

1. **It answers a question you already had answered.** Aboutness is recoverable from the filename and the content, and search does it better than folders. Treatment is not recoverable from content at all. Spending your one structural signal on the recoverable question wastes it.
2. **It shreds every concern across kinds.** "Security" is simultaneously a runbook (rotate the keys), a spec (the auth contract), a record (last quarter's audit), and documentation (the current threat model). A `security/` folder puts four incompatible lifecycles in one directory, and now no rule applies to its contents — which is exactly the state you were trying to escape.
3. **It has no closure.** Topics are unbounded; new ones arrive with every initiative. Lifecycles are bounded: there are only so many relationships a document can have to time. A bounded set can be an exhaustive rule. An unbounded one can only ever be a list you maintain.
4. **It rots asymmetrically.** When an initiative ends, its topic directory becomes a graveyard nobody dares delete — indistinguishable, from the outside, from a live one.

> **The tell.** If you can't say what a directory's contents *promise a reader*, it's a topic bucket.
> `docs/` promises "this is current." `decisions/` promises "this is history." `security/` promises
> nothing.

**Routing topics without topic buckets** — the artifact keeps its concern in its *name*, and its
bucket from its *kind*:

| Artifact | Goes to | Because |
|---|---|---|
| CI/CD pipeline definition | `.github/workflows/` | The harness parses it — the path is API |
| Deploy or rollback procedure | `runbooks/` | Executed again |
| Test plan | `runbooks/` | Executed again |
| A QA round's results | `decisions/` | A record of one execution |
| Eval harness config | `specs/` or the owning test tree | Parsed |
| Eval *results* | `decisions/evals/` | Generated data (§7) |
| Threat model (current) | `docs/` | Describes the system as it is |
| Security audit (dated) | `decisions/` | A record of a moment |
| Compliance policy | `docs/` | Current and binding |
| Vendor attestation | `decisions/vendor/` | Correspondence, frozen |
| Postmortem | `decisions/` | A record of a moment |
| Spike / investigation writeup | `decisions/` | A record of a moment |
| Architecture narrative | `docs/arch/` | Describes the system as it is |
| Invariant spec cited by code | `docs/` | Must change when the invariant changes |

That last row is a real correction from practice: a state-machine invariant spec was filed in
`decisions/` during a restructure, and fourteen source files cited it as authority. It fails the
`decisions/` test outright — the code depends on it being *current*, so it must be maintained — and
it moved to `docs/arch/`. **A record you would need to edit after it goes terminal is not a record.**

---

## 6. The rules

### The birth rule

> A new markdown file is born in `decisions/` with `> **Status:** Proposed`, unless it passes another
> bucket's membership test **on day one**.

Not "unless it might later become documentation." On day one. Most documents that feel like emerging
documentation are actually records of a decision being made, and they stop changing the moment the
work ships. Defaulting to `decisions/` means the failure mode is a record that should be promoted —
visible and cheap — rather than a stale record impersonating documentation (§4).

### The freeze rule — status, not directory

> A record with a **terminal** status (`Shipped`, `Superseded-by`) is frozen: append a status-header
> line, never rewrite the body. A record marked `Proposed` or `In-progress` is **live** — edit it
> freely until it reaches a terminal status.

This is a correction, and the correction is instructive. The rule originally froze the whole
directory: *nothing in `decisions/` may be edited except its header.* That is wrong, and a code
review caught it. In-flight trackers legitimately live in `decisions/` — they are records of work
being decided *right now* — and under a directory-wide freeze the next engineer to fix an invariant
was **forbidden from updating the document defining it**. Code and spec would diverge with nowhere
sanctioned to record the drift.

The generalizable lesson: **a rule that attaches to location will eventually forbid something
legitimate, because location is a proxy.** Attach the rule to the property you actually care about.
Here that property is status, and status is already written in the file.

Corollary: repairing a **link** inside a frozen record — a target or a label that points at a moved
file — is navigation metadata, not the decision. Allowed, and necessary; otherwise every file move
strands the historical record.

### Path stability

Anything under `specs/`, plus any file whose raw URL is fetched by another repository, is **public
API**. Moving it is a breaking change. Two specific traps:

- **A stub that returns 200 fails silently.** Leaving a "moved" pointer at a URL that automation `curl`s does not preserve the contract — the consumer gets a redirect note with a success code and no way to detect the difference. If machines consume it, the payload stays; the pointer goes at the *new* location. If humans consume it, a 404-then-pointer is fine, because a human reads the pointer.
- **Seeded-template paths belong to the *generated* repo, not yours.** If your tooling writes `docs/architecture/` into a repository it scaffolds, that string is a contract with every repo you have ever seeded. A well-meaning sweep that "fixes" it to match your own tree corrupts all of them. Keep an explicit allow-list, and make your reference checker aware of it.

---

## 7. Generated artifacts are not records

A scorecard a script writes is **data**. The verdict a human writes on top of it is a **decision**.
Collapsing the two destroys the second.

This is not hypothetical: a model bake-off script was pointed at a curated `decisions/` record, and
every run overwrote the whole file — deleting the hand-written supersession note that was the only
part anyone needed.

| | Generated artifact | Curated record |
|---|---|---|
| Lives in | `decisions/evals/` | `decisions/` |
| Written by | a script, every run | a human, once |
| Filename | `YYYY-MM-DD-<slug>.md` | `YYYY-MM-DD - Title.md` |
| Header | `> **Generated artifact**` + the command | `> **Status:**` |
| Edited | never — a re-run writes a *new* dated file | header only, once terminal |
| Status lint | exempt | enforced |

The curated record **cites** the artifact it drew its verdict from. Then regenerating the evidence can
never rewrite the conclusion.

> **Rule.** Never point a generator at a curated record. If a tool writes it, the destination is a
> dated file the tool owns exclusively.

---

## 8. Enforcement — a taxonomy nobody checks is a preference

Conventions decay at exactly the rate they are unenforced. Four checks, all cheap, all in CI:

| Check | Catches |
|---|---|
| Every reference resolves — in markdown links **and source comments** | The overwhelming majority of rot after any file move |
| Link **labels** resolve, not just targets | A label reading `../OldPath.md` pointing at a valid target. Agents copy the visible label, not the href |
| Every `decisions/` record has a `> **Status:**` header | Records that silently become undated, unattributed prose |
| Root markdown is exactly the sanctioned files | The slow accretion that makes root meaningless |

### The lesson that matters more than the checks

A restructure moved ~130 files. The guard reported `doc links OK` throughout, and that was read as
evidence the sweep was complete.

It was not evidence of much. The checker read only `*.md` and matched a single regex for inline link
syntax. It could not see the **~282 stale references sitting in `.py`, `.ts`, `.tsx`, `.sh` and
`.yml` source comments** — the largest class of breakage by an order of magnitude. It also failed in
the other direction, red-lighting correct documents, because it had no code-fence awareness (a file
*demonstrating* link syntax became a failure) and truncated paths at the first parenthesis.

> **A green guard is evidence only to the extent the tool can see the failure.** Before trusting a
> clean run, ask what the checker physically cannot examine — and treat that blind spot as unverified
> rather than clean.

Three corollaries earned the hard way:

- **Check every tracked text file, not just markdown.** Source comments are where path references actually live, and they are invisible to a docs-only linter.
- **Resolve against the version-control index, not the working tree.** A gitignored file present on a developer's disk passes locally and 404s in CI on the same commit; a case-only mismatch passes on a case-insensitive laptop and fails on a Linux runner. A guard that answers differently depending on where it runs teaches people to disbelieve it.
- **Do not put a path filter on the guard's CI trigger.** A filter that must enumerate every linkable asset type (`png|jpg|svg|yaml|sh|…`) is itself a recurring bug: rename an image directory, touch no markdown, and the job never runs — so the breakage lands on the main branch and surfaces later attached to an innocent pull request. The job takes seconds. Run it on everything.

And test the guard itself. The checker above had no tests, which is precisely why it could be so
confidently wrong for so long. A fixture per historical defect, and a mutation check that each
fixture actually fails when you revert the fix it guards.

---

## 9. How this survives the age of context engineering

Everything above is defensible as ordinary hygiene. What makes it *load-bearing* is what happens when
the primary reader is a model.

**1. The tree is retrieval you don't pay tokens for.** Context windows are finite and every retrieval
strategy has a cost. A path is free: it is already present in every file listing, search result, and
tool output, before a single byte of content is read. Encoding treatment into the path means an agent
can decide *not to open* a file — the cheapest possible outcome — using information it already has.

**2. Staleness becomes machine-readable.** `> **Status:** Superseded-by: X` is a fact a model can act
on. Without it, a superseded design doc is indistinguishable from current architecture, and the model
will read it with full confidence. The status header is a two-word contract that converts an
unanswerable judgement into a lookup.

**3. Bindingness prevents the most expensive agent failure.** An agent that edits a frozen record
destroys history that cannot be reconstructed. An agent that treats a `vision/` PR-FAQ as a
specification builds a product nobody asked for. Both are prevented by the path, before the model has
to exercise judgement it does not have.

**4. It gives `/clear` a defined restart.** Context compaction is now routine, and the recurring
question is *what do I re-read?* The taxonomy answers it in a fixed order: `README.md` (what this is)
→ `CLAUDE.md` (how to work here) → `docs/` (what it consists of) → then, on purpose, the specific
record that explains why. That is a **reading order**, not a folder list, and it is the single most
useful thing to hand a freshly-cleared session.

**5. It survives without infrastructure.** No vector database, no index to rebuild, no embedding
pipeline to keep warm, nothing to drift out of sync with the tree. The semantics live in the path, so
they are correct by construction and versioned with the code. Retrieval infrastructure is a fine
addition; it is a terrible dependency for something this fundamental.

**6. It degrades gracefully.** See the growth valves below. A taxonomy that only works at 50 files is
a taxonomy that will be abandoned at 500 — and it will be abandoned at the exact moment it starts to
matter.

**7. It makes provenance a first-class question.** As more of the tree is model-generated, "who wrote
this and was it verified" becomes load-bearing. A generated artifact carries the command that produced
it (§7); a curated record carries a human status. The distinction is in the tree, so it survives the
author leaving.

### Growth valves

| Pressure | Valve |
|---|---|
| `decisions/` exceeds ~100 flat files | Shard by year: `decisions/2026/`. Chronology is already in the filename, so nothing needs renaming. |
| `tasks.md` accumulates completed sections | Archive into `decisions/` at release boundaries. The ledger becomes a record — which is what it always was. |
| A `docs/` file is only ever read by one subsystem | Move it next to that subsystem. `docs/` is for cross-cutting understanding, not a dumping ground for all prose. |
| Two records keep getting edited together | They are one record. Merge them, or link them with `Pairs-with`. |
| A record needs body edits after going terminal | It is misfiled. It is documentation — promote it to `docs/` (§5). |

### The five-year test

Run any candidate taxonomy against this before adopting it:

1. **A new artifact type nobody anticipated arrives** — an eval suite, an agent trace, a red-team report. Is there a rule that places it without a meeting? *(Topic buckets fail here. Lifecycle buckets don't.)*
2. **Someone leaves.** Can a newcomer tell current documentation from a two-year-old design doc without asking anyone? *(Status headers.)*
3. **The tree triples.** Does the rule still hold, or does one directory become an unsearchable pile? *(Growth valves.)*
4. **An agent works unattended.** Can it tell what it may edit from what it must not? *(Freeze rule, in the path and the header.)*
5. **A tool consumes a path.** Is it obvious which paths are API, so a refactor doesn't break a repo you don't own? *(`specs/`, plus the seeded-template allow-list.)*

---

## 10. Applying it to your repository

**Do not copy the six buckets.** Copy the axis. Classification follows what a repository *is*.

This repository is the demonstration. **ContextEng is a prompt-and-template library, not a product**,
so its shape is four buckets, not six:

| ContextEng bucket | Membership test |
|---|---|
| root + `.claude/` | Fetched or seeded verbatim into another repo — **the path is public API** |
| `prompts/` | Text you point a model at, parameterized for reuse; never describes this repo |
| `docs/` | Methodology and governance a human or model reads for understanding |
| `utils/` | Executable tooling |

There is no `decisions/` here, because this repository does not accumulate one-time records — it
accumulates reusable text. There is no `runbooks/`, because there is nothing to operate. Adding
either "for consistency" would create empty directories that teach a reader nothing, which is the
cargo-cult failure this document exists to prevent.

The axis is what transfers, and it produced both shapes:

1. **Enumerate what you actually have.** Every non-code file. Do not design in the abstract; the surprises are in the inventory.
2. **For each, answer the three questions** (§2): audience, lifecycle, bindingness.
3. **Group by the answers.** Your buckets are whatever clusters emerge. If you get six, fine. If you get three, that is the right number for your repository.
4. **Write the membership test as a sentence a stranger could apply** — a question, not a category name. "Is this parsed by a machine?" is a test. "Specs" is a label.
5. **Fix the root.** Decide the small set an agent loads unconditionally, and enforce it.
6. **Adopt the status header** even if you adopt nothing else. It is the cheapest change here and the highest leverage — one line per record turns "is this still true?" from a judgement into a lookup.
7. **Automate the checks in §8, and test the checker.**

**The migration order that works**, from doing it: security-sensitive deletions first · moves second,
in `git mv` batches so history follows · reference sweep third · guard last — and then re-run the
sweep, because the guard will find what you missed. Expect the reference count to be **an order of
magnitude larger than your estimate**, because the estimate will be scoped to markdown links and the
reality is mostly source comments.

---

## See also

- [`CLAUDE.md`](../CLAUDE.md) — carries the taxonomy as an enforceable constraint for repositories seeded from this one
- [`docs/AGENTCORE_FIRST.md`](AGENTCORE_FIRST.md) — the same "decide it deliberately at t=0" posture, applied to the agent runtime
- [`prompts/Code-Reviewer.md`](../prompts/Code-Reviewer.md) — emits its transcript into `decisions/` with a status header, per §4
