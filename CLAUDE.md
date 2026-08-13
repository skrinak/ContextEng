# CLAUDE.md

> Template for AI-DLC projects seeded from ContextEng. Architecture is
> **AgentCore-first**: if the product has an agent/LLM loop, that loop runs on
> Amazon Bedrock AgentCore from t=0 — not as a Lambda behind API Gateway you
> migrate later. AgentCore's value is *infrastructure you delete*, not features you
> add. Two prerequisite decisions before designing the backend — the
> **Harness-vs-Runtime** fork and the **deterministic-first** gate — plus the
> primitive ledger and migration gotchas are in
> [`docs/AGENTCORE_FIRST.md`](https://github.com/skrinak/ContextEng/blob/main/docs/AGENTCORE_FIRST.md). Read it first.
>
> **Built for teams, not standalone developers.** These products are built and
> operated by teams inside an org, so default to shared, governed, discoverable
> infrastructure: immutable versions + named endpoints + rollback (so concurrent
> developers and deploys don't break each other), one source of truth per domain
> taxonomy (never a per-developer copy), Policy as the shared guardrail, and
> **Registry** to publish/discover agents, tools, and MCP servers across teams
> instead of each team rebuilding what already exists.

## Constraints

Never do these things:

- Never propose or implement workarounds, shortcuts, or stopgap fixes that introduce tech debt. Diagnose the root cause and design a lasting solution. When a lasting fix is not feasible now (cost, scope, upstream dependency), surface that constraint explicitly so the trade-off is a deliberate decision — not a quietly-shipped band-aid.
- **Agent code lives in the AgentCore Runtime (or Harness), not in Lambda.** The agent path is Frontend → AgentCore Runtime (direct SigV4) → Bedrock + Memory + Gateway + Identity + Policy. Building the agent loop as a Lambda behind API Gateway hits the 29-second sync timeout and forces a `turnStatus="generating"` self-invoke + frontend-polling state machine — a permanent class of async-vs-state races that AgentCore exists to delete. Runtime sessions run up to 8 hours and stream progress.
- **Deterministic-first: compute the answer when you can, generate it only when you must.** The model is the slowest, costliest, least reproducible component — reach for it last. Token cost, not model quality, is what kills agents in production (multi-agent loops use ~15× chat tokens; full history is re-sent every turn, so real loops cost 5–10× the naïve estimate). Route each requirement down three rungs: (1) plain code computes it (lookup, rule, arithmetic, validation, join) → CRUD path, no model call; (2) needs judgment in one bounded spot → a single structured / function-calling model call inside deterministic Python (router, classifier, extractor, judge); (3) genuinely un-hardcodable but verifiable → an agent loop on the Runtime. "AgentCore from t=0" means rung 3 already runs on AgentCore — *not* that every feature starts at rung 3.
- **Never add a custom proxy layer, and never run FastAPI or FastMCP as a standalone always-on process outside AWS-managed compute.** The banned thing is the hosting model (a bare `uvicorn`/`fastmcp run` on an EC2 box or non-AWS VPS), not the framework. CRUD path: Frontend → API Gateway (REST) → Lambda. Agent path: Frontend → AgentCore Runtime/Harness via Cognito Identity Pool SigV4 — direct invoke is *not* a proxy layer. **Tool/MCP servers** — including FastMCP- or FastAPI-built ones — are packaged as Lambda functions or Fargate containers and exposed through AgentCore Gateway (a FastAPI OpenAPI spec is a first-class Gateway target), never as a process reachable outside Gateway's auth and policy boundary. See [AGENTCORE_FIRST.md §5](https://github.com/skrinak/ContextEng/blob/main/docs/AGENTCORE_FIRST.md).
- Never ship Strands (or any agent SDK) as a Lambda Layer. It ships inside the Runtime container's own `pyproject.toml`. SDK bumps are a one-line edit + redeploy, no layer rebuild.
- Never LLM-drive routing or orchestration. Deterministic Python decides *when* to call the model; the LLM adds wisdom inside clearly-bounded helpers. The orchestrator is plumbing, not an agent.
- Never hardcode mock data in source code. Test/mock data is acceptable only when loaded from a data source (fixtures, seed files, test APIs).
- Never deploy outside your designated region.
- Never create, move, or edit a file without applying **[The tree](#the-tree--how-to-place-read-and-change-files)** below. It is not a filing preference; it is how this repository tells you what is true, what is binding, and what you may change.
- Never commit code unless the user explicitly asks.
- Never add code comments unless the user explicitly asks.
- Never call python or pip directly. Use `uv run` for execution, `uv pip` or `uv add` for package management. uv is a prerequisite.

## Harness vs Runtime — the first architectural decision

Two ways to run the loop. Decide deliberately before anything else; both are GA.

- **Runtime (code-based loop) — ContextEng's default.** You write the orchestration loop in Python (entrypoint + op-dispatch); invoke via `InvokeAgentRuntime` (SigV4); any framework (Strands, LangGraph, CrewAI, LlamaIndex, Google ADK, OpenAI Agents, or raw custom). Buys an auditable state object, in-loop gating, prompt-cache control, speculation skips, and status short-circuits. The "never LLM-drive orchestration" rule *is* a code-based-loop choice — when the orchestration doctrine is the product, write the loop.
- **Harness (managed loop).** Declare model + system prompt + tools + skills + memory as config; invoke via `InvokeHarness`; AgentCore runs the loop, immutable versions, named endpoints, rollback, and mid-session model switching. Right when the loop is conventional (retrieve → reason → call tools → answer), orchestration is not itself the product, and you want production-grade in hours. Built on Runtime; can `export to Strands code` later.

Default Runtime unless the loop is conventional *and* speed-to-prod outweighs deterministic control. Either way, pin deploys to named endpoints + immutable versions so concurrent developers and deploys don't clobber each other.

## Before every task

1. Track work in tasks.md. Update status immediately. Never use tasks.txt or other variants. For multi-phase migrations, track substep deferrals in the task tool, not in the design doc.
2. Run lint/typecheck before marking work complete:
   - Web: `npm run lint` and `npm run typecheck`
   - Python: check pyproject.toml for lint commands (ruff, mypy, pylint)
   - CloudFormation/CDK: `npx cdk synth`, `cfn-lint`
   - Terraform: `terraform validate`, `terraform fmt -check`, `tflint`

## Before modifying code

1. Read before writing. Before modifying a function or module, read every file that imports or calls it. Do not skip this step.
2. Match existing patterns. If the codebase already solves a similar problem, use that approach. Do not introduce new patterns, libraries, or abstractions when an existing one works.
3. Analyze dependencies: helper functions, imports, type definitions.
4. Verify API response structure before relying on it.
5. Test after any code removal. Even small deletions can cascade. Destructive deletes are only safe once the calling surface is provably dead.

## Code standards

- Backend: Python 3.12+ with strict typing.
- Frontend: TypeScript with strict typing.
- Security: client-side encryption for sensitive data, all API keys in .gitignore.
- Infrastructure: CDK/CloudFormation only, templates in backend/infrastructure/.
- Observability: use `logging.getLogger(__name__)`, never `print()` — OTEL auto-instrumentation attaches trace context to every log line.

## Architecture — AgentCore first

Two compute paths from the browser. The agent path is architecturally **primary** (the distinctive plane this design is about); by volume, deterministic-first means the CRUD path should carry most work. They never call each other — they share state through DynamoDB / AgentCore Memory.

```
Browser (React / TypeScript)
  ├─ Agent path (PRIMARY):  Cognito Identity Pool SigV4 → AgentCore Runtime (or Harness)
  │                           → Bedrock · Memory · Gateway · Identity · Policy · Observability
  │                         ↳ streaming envelope over SSE or bidirectional WebSocket:
  │                           *_started → heartbeat {elapsedS} (2s) → *_complete
  └─ CRUD path (support):   Cognito JWT → API Gateway (REST) → Lambda → DynamoDB
```

No API Gateway hop and no proxy fleet on the agent path — the browser invokes the Runtime directly with Cognito Identity Pool authenticated-role credentials. Runtime streams over **SSE and bidirectional WebSocket**; there is no SSE-only restriction.

**AgentCore primitives** — adopt the ones your product needs; each is infrastructure you don't write, deploy, monitor, or debug:

| Primitive | Status | Replaces | What you write instead |
|---|---|---|---|
| **Runtime** | GA | Self-invoke async pattern, `turnStatus` state machine, 29s-timeout dance | Op-dispatch entrypoint + streaming envelope |
| **Harness** | GA | The orchestration-infra layer (loop, versioning, model-swap plumbing) | Config: model + prompt + tools + skills + memory |
| **Memory** | GA | DynamoDB dialogue table, dual-write coordination, embedding pipeline | `session_manager` wiring (or `list_events`/`create_event`) |
| **Gateway** | GA | Hand-rolled HTTP clients + per-tool credential plumbing | OpenAPI / Smithy / Lambda target per tool |
| **Identity** *(workload/outbound only — NOT human sign-in)* | GA | Hand-rolled outbound OAuth, JWT signing, signature validation | A declared credential provider |
| **Policy** | GA | Imperative gates (`require_admin_class()`), quota counters | Cedar (or natural-language) policies at the Gateway boundary |
| **Observability** | GA | `print()` + Athena heroics, manual token accounting | `logging` + OTEL spans (default-on) |
| **Code Interpreter** | GA | Self-managed code-exec sandbox / jailing | `code_session` or framework tool wrapper |
| **Browser Tool** | GA | Self-hosted headless-browser fleet | A managed browser session (CDP over SigV4) |
| **Registry** | Preview | Tool/agent sprawl — teams rebuilding MCP servers & agents they can't find | Published catalog records (hybrid search, publisher→curator→consumer approval); adopt at org scale |
| **Evaluations** | Preview | Ad-hoc prompt smoke tests | LLM-as-judge rubric wired into the deploy |

**What stays in product code** — AgentCore has no opinion about these, correctly: the orchestration doctrine (surgical Python deciding *when* to call the LLM), your domain state object (coverage, ledger, completed/skipped work), your aspect/role/task definitions, your prompt disciplines, and the in-loop auditor that gates progress (distinct from the post-hoc Evaluator). That is the IP. Everything in the table is infrastructure you rent; everything here is the product you build.

### Build into the runtime from t=0

The SDK owns the HTTP server on `:8080`, SSE framing, the `/ping` health route, and a dedicated worker event loop on a background thread. The entrypoint is three lines (`BedrockAgentCoreApp()` + `@app.entrypoint` + `app.run()`); an async-generator handler auto-streams as `text/event-stream`. Don't re-implement those. You own:

- **Uniform streaming envelope on every op** (`*_started` immediately → `heartbeat {elapsedS}` every ~2s when work exceeds ~5s → terminal `*_complete`). Even sub-second ops use it, so the frontend handler never branches on op shape.
- **Anthropic prompt-caching** (`cachePoint`) on every agent system prompt — 30–50% prefill cost/latency cut, ~90% off cached-prefix reads, break-even at two requests (5-min TTL). Keep the cached prefix byte-stable; a timestamp or UUID in the system prompt silently invalidates it.
- **Status-aware ops** — bake state-machine short-circuits (e.g. an approval state that writes directly without firing the orchestrator) into the op from the start: one op for the frontend, status-aware on the server.
- **OTEL on by default** — `aws-opentelemetry-distro` in deps; the generated Dockerfile wraps the entrypoint with `opentelemetry-instrument`; `AGENT_OBSERVABILITY_ENABLED=true`.
- **Evaluator in the same deploy**, so a prompt can never ship without a regression check.
- **Async:** `asyncio.run()` raises inside the Runtime loop and `nest_asyncio` breaks the server — lean on the SDK's worker loop. If you drive your own stream, use a `concurrent.futures.ThreadPoolExecutor` with its own loop.

### Frontend transport (load-bearing)

- AWS SDK JS `FetchHttpHandler({ requestTimeout: 300_000 })` / boto3 `read_timeout=900, retries={"max_attempts": 0}` — the ~30s default kills long turns.
- Read the body with a `getReader()` loop, **not** `for await…of` (patchy pre-Chrome 124). boto3: `resp["response"].read()`; the request payload is bytes (`json.dumps({...}).encode("utf-8")`).
- Explicit `break` on the terminal event — stream EOF doesn't propagate cleanly through CloudFront + Runtime proxies.
- `runtimeSessionId` must be ≥ 33 chars — use a UUID; reusing it pins session affinity to the same warm microVM.
- Parse model output with `json.JSONDecoder().raw_decode(stripped)`, not `json.loads()` — long contexts emit trailing post-JSON commentary.
- Expose agent mutations through RTK Query `queryFn → invokeRuntimeOnce(...)` so transport changes need zero call-site edits.

## Stack / Auth / Security

- **Region:** one region only (pick yours); us-east-1 is the exception only for a CloudFront ACM cert.
- **Auth — two layers, don't conflate them:**
  - *Human sign-in* is **Cognito's** job: Cognito User Pool (JWT for the CRUD path) + federated IdPs for SSO (Google native OIDC, GitHub via a small OIDC bridge since GitHub isn't OIDC, enterprise via SAML/OIDC or a WorkOS bridge). Plus a Cognito Identity Pool authenticated role (SigV4 for direct Runtime invoke) — grant it `bedrock-agentcore:InvokeAgentRuntime`. Federated SSO design: [`docs/FEDERATED_SSO.md`](https://github.com/skrinak/ContextEng/blob/main/docs/FEDERATED_SSO.md).
  - *Workload/outbound* auth (the agent acting on a user's behalf against external services) is **AgentCore Identity**. The two layers meet only at a `custom:*` claim carrying your canonical user id. AgentCore Identity is not your login system.
- **Security:** SOC2 foundation, TLS 1.2+, KMS on all DynamoDB tables, Secrets Manager for residual runtime secrets, IAM least-privilege per function/role. Prefer Identity/Gateway credential providers over hand-managed Secrets Manager entries for tool auth.
- **Compute economics:** serverless by default; past a sustained-utilization threshold, move that workload to Fargate or Savings-Plan EC2 — stay AWS-native either way, never a self-managed VPS.
- **Regulated (FSI) workloads:** regimes in [`docs/FSIregulation.md`](https://github.com/skrinak/ContextEng/blob/main/docs/FSIregulation.md). AWS/AgentCore attestations make compliance evidence cheaper to produce, but "eligible" ≠ "compliant" — data classification and configuration remain yours. EU financial-entity scope triggers DORA concentration-risk / exit-strategy obligations: keeping domain/orchestration code portable with AWS calls isolated behind an interface (`domain/`, per [AGENTCORE_FIRST.md §4.2](https://github.com/skrinak/ContextEng/blob/main/docs/AGENTCORE_FIRST.md)) *is* your exit-strategy evidence — not a reason to self-host.
- **Data:** name resources on the product brand from t=0 (a rename later forces full resource recreation). No data caching unless explicitly designed.

## The tree — how to place, read, and change files

The directory a file sits in is **metadata you must act on**. It tells you whether the contents are
true now, whether you may edit them, and whether something parses the path. You cannot recover any of
that from the file's prose: a superseded design doc and current architecture read identically.
Reference implementation: [skrinak/groundwork](https://github.com/skrinak/groundwork). Rationale:
[REPOSITORY_TAXONOMY.md](https://github.com/skrinak/ContextEng/blob/main/docs/REPOSITORY_TAXONOMY.md).

### Placing a file — run in order, stop at the first match

0. Was it emitted by a tool or a session rather than authored, **and** does everything durable in it
   already live elsewhere? → **`scratch/`** (ignored, never tracked). The narrowest test in the list —
   answer it honestly or you will lose something.
1. Does a machine parse it (test fixture, CI job, code generator, another repo)? → **`specs/`**. The path is now API.
2. Will an operator execute it again, step by step? → **`runbooks/`**
3. Does it describe the system **as it is**, such that leaving it unchanged after a system change would be a bug? → **`docs/`**
4. Does it describe intent rather than reality? → **`vision/`**
5. Is it consumed by you or the harness rather than read by a human for understanding? → **`.claude/`**
6. Otherwise → **`decisions/`**, named `YYYY-MM-DD - Title.md`, with `> **Status:** Proposed`

Root markdown is **closed**: `README.md`, `CLAUDE.md`, `tasks.md`. Never add a fourth — root is what
gets loaded unconditionally every session, so anything there costs tokens on every task forever. Never
create a topic folder (`security/`, `qa/`, `evals/`, `notes/`): one concern spans four lifecycles, and
a topic bucket gives you no rule for the next artifact type.

**Ignoring a file is not filing it.** `.gitignore` protects the remote; the tree is what a reader and
a model actually see. An untracked transcript in `docs/` is still in `ls`, still in glob, still in a
file search, and it still makes `docs/`'s claim about itself. Transient output goes in `scratch/` — a
treatment class, not a topic, and the zero point of the same obligation scale the other buckets grade.

If two rules seem to fit, the **earlier** one wins — a parsed contract is a spec even if it also
documents, and a procedure is a runbook even if it also explains.

### Before you edit — what each bucket permits

| Bucket | You may | You must not |
|---|---|---|
| `docs/` | Edit freely. **You are obliged to update it in the same change** that alters what it describes | Let it drift. A stale file here poisons the one bucket that is supposed to be trustworthy |
| `specs/` | Edit content as the contract evolves | Move or rename before auditing every consumer, including other repos and raw URLs |
| `runbooks/` | Edit freely; add gotchas as you hit them | Leave a step that no longer matches reality |
| `decisions/` | Edit the body **only** while status is `Proposed` or `In-progress` | Rewrite the body once status is `Shipped` or `Superseded-by:` — **append a status line instead** |
| `vision/` | Edit freely | Cite it as evidence of how the system behaves today |
| `.claude/` | Edit skills, commands, hooks | Commit `settings.local.json`; overwrite a `SKILL.md` (its frontmatter is what registers the skill) |
| `scratch/` | Put anything transient here; delete the contents at any time without asking | Store the only copy of anything, or a credential — `.gitignore` protects the remote, not your disk |
| root trio | Keep current | Add a fourth file |

**Repairing a link inside a frozen record is always allowed** — that is navigation, not the decision.
Otherwise every file move strands the historical record.

**A terminal record that needs body edits is misfiled.** It is documentation. Move it to `docs/` rather
than editing it in place.

### When sources disagree, trust in this order

1. **The code** — ground truth, always
2. **`specs/`** — for anything a machine parses; the contract wins over prose about the contract
3. **`docs/`** — for how the system behaves
4. **`decisions/`** — for *why*, and only as of that record's status date. A `Shipped (2026-01)` record describes January, not today
5. **`vision/`** — intent only. Never evidence of current behavior

Never resolve a contradiction by editing a frozen record. Fix `docs/`, and if the divergence is
important, write a **new** record that supersedes the old one and add `Superseded-by:` to the original.

### After `/clear`, read in this order

`README.md` (what this is) → `CLAUDE.md` (how to work here) → `tasks.md` (what is in flight) →
`docs/PRD.md` (what it consists of) → then, deliberately, the one record explaining the area you are
about to touch. Do not bulk-read `decisions/`; it is history, and most of it is not about your task.

### Writing a record

```markdown
# 2026-07-28 - What Was Decided

> **Status:** Proposed
> **Pairs-with:** 2026-07-28 - Its Execution Ledger.md
```

The status line must be the first line after the H1 — CI fails without it. Statuses: `Proposed` ·
`In-progress` · `Shipped (YYYY-MM-DD)` · `Superseded-by: <path>`. Write records in the past tense and
include a **Consequences** section; that is the part a future reader returns for.

### Generated output

Anything a script writes goes to **`decisions/evals/`** as `YYYY-MM-DD-<slug>.md` with a
`> **Generated artifact**` header and the producing command. Never point a generator at a curated
record — every run silently deletes the human reasoning, which is the only part anyone needed.

### Before moving anything

`grep` the whole repo for the old path — **including non-markdown source**, where most references
actually live — then check raw URLs other repos may fetch. A stub that returns HTTP 200 does not
preserve a machine-facing contract: the consumer gets a pointer with a success code and no way to
detect the substitution. Run the reference guard (`make check-links`) before and after.

## Project structure

AgentCore-first layout. Agent code is in `backend/runtime/`; `backend/lambda/` is CRUD-only.

```
YOUR_APP/
├── .env                         # Local dev only
├── backend/
│   ├── runtime/                 # AgentCore-managed agent container (the agent path)
│   │   ├── app/coordinator/
│   │   │   ├── main.py          # BedrockAgentCoreApp entrypoint, op-dispatch
│   │   │   ├── runner.py        # one function per op (turn, advance, elaborate, …)
│   │   │   ├── llm.py           # surgical model helper over the framework's model class
│   │   │   ├── domain/          # orchestration doctrine + domain state object (product IP)
│   │   │   ├── agents/          # framework-agnostic agent/tool factory (Strands, LangGraph, …)
│   │   │   ├── aspects/         # aspect/role/task specs (product IP)
│   │   │   ├── memory/          # AgentCore Memory client (avoid dir names that collide
│   │   │   │                    #   with top-level dependency packages — CodeZip drops them)
│   │   │   └── mcp_client/      # Gateway MCP client
│   │   └── agentcore/
│   │       ├── agentcore.json   # runtime + memory + gateway + identity + evaluator spec
│   │       └── schemas/         # OpenAPI / Smithy schemas for Gateway tool targets
│   ├── infrastructure/          # CDK for the CRUD path + auth + storage
│   │   └── lib/
│   │       ├── api-stack.ts      # API Gateway + slim CRUD lambdas
│   │       └── auth-stack.ts     # Cognito User Pool + Identity Pool + RuntimeInvoke grant
│   └── lambda/                  # CRUD ONLY — no agent code lives here
├── docs/                        # The system AS IT IS — living; arch/ narratives + diagrams
├── specs/                       # Machine-parsed — the path is API
├── runbooks/                    # Procedures an operator runs again
├── decisions/                   # One-time records; frozen once terminal. evals/ = generated
├── vision/                      # The product intended, not the system that exists
├── .claude/                     # Skills, commands, hooks — model-facing
├── scratch/                     # Transient: session exports, tool output — ignored, never tracked
├── frontend/
│   └── web/                     # React TypeScript app
│       └── src/services/        # runtimeClient.ts, useDialogueStream.ts, invokeRuntimeOnce.ts
├── README.md · CLAUDE.md · tasks.md   # the closed root trio
└── utils/                       # Scripts and tools, incl. the reference guard
```

Every directory carries a `README.md` stating what belongs in it. **Read the one next to the file you
are about to create** — it holds the membership test verbatim, so you never have to come back here.

## Infrastructure reference

The CRUD plane and the agent plane are **separate CDK apps** (the agent plane is provisioned via the AgentCore CDK from `agentcore.json`). Keep account-bound identifiers (Runtime ARN, Memory ID, KMS key, Cognito IDs, CloudFront IDs) in CDK context, not scattered literals — a fresh-account migration must re-point them in lockstep.

Fill in per project:

- DynamoDB tables (CRUD state only — Memory holds dialogue): [specify]
- AgentCore Runtime / Memory / Gateway IDs: [specify]
- Gateway tool targets (OpenAPI/Smithy schemas): [specify]
- API Gateway endpoints (REST, CRUD only): [specify]
- Admin APIs (require x-admin-email header): [specify]

## Tooling & deployment

Standardize on the **new CLI** `@aws/agentcore` (npm, Node 20+) with config artifact `agentcore.json`. The legacy `bedrock-agentcore-starter-toolkit` (pip; `configure`/`launch`; hidden `.bedrock_agentcore.yaml`) prints a deprecation banner — new projects don't use it. Run uv initialization before any AWS commands (see `runbooks/UV Setup.md`).

```bash
agentcore create --name MyAgent --framework Strands --model-provider Bedrock --build CodeZip
agentcore dev                 # local server, hot reload, agent inspector on :8080
agentcore deploy --plan       # preview the CDK diff
agentcore deploy              # build + deploy (CDK synth/deploy under the hood)
agentcore invoke --prompt "..." --stream
agentcore add memory|gateway|credential|evaluator   # attach primitives
agentcore registry publish|search                   # publish/discover org agents, tools, MCP servers
```

The Dockerfile is generated, not hand-written. Build types: CodeZip (default) or Container (bring-your-own).

Deploy: the agent plane deploys via `agentcore deploy` (raw `cdk deploy` is the documented fallback when bootstrap is unhealthy — fix the bootstrap, don't live on the workaround). The CRUD plane deploys via `npx cdk deploy --all` with domain/cert context flags (those flags are load-bearing — omitting them silently drops custom-domain CORS and flips frontend URLs to the CloudFront domain).
