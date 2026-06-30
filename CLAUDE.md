# CLAUDE.md

> Template for AI-DLC projects seeded from ContextEng. Architecture is
> **AgentCore-first**: if the product has an agent/LLM loop, that loop runs on
> Amazon Bedrock AgentCore from t=0 — not as a Lambda behind API Gateway you
> migrate later. AgentCore's value is *infrastructure you delete*, not features you
> add. Two prerequisite decisions before designing the backend — the
> **Harness-vs-Runtime** fork and the **deterministic-first** gate — plus the
> primitive ledger and migration gotchas are in
> [`docs/AGENTCORE_FIRST.md`](docs/AGENTCORE_FIRST.md). Read it first.
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
- Never add a FastAPI or Express **proxy layer**. CRUD path is Frontend → API Gateway (REST) → Lambda. The agent path calls AWS-managed serverless agent services (AgentCore Runtime) directly from the frontend via Cognito Identity Pool SigV4 — that is *not* a proxy layer. Two compute paths, no custom proxy fleet. This rule is written around the principle ("no custom proxy layers in front of managed services"), not the literal ("everything goes through API Gateway"); a literal ages badly — see `docs/AGENTCORE_FIRST.md` §5.
- Never ship Strands (or any agent SDK) as a Lambda Layer. It ships inside the Runtime container's own `pyproject.toml`. SDK bumps are a one-line edit + redeploy, no layer rebuild.
- Never LLM-drive routing or orchestration. Deterministic Python decides *when* to call the model; the LLM adds wisdom inside clearly-bounded helpers. The orchestrator is plumbing, not an agent.
- Never hardcode mock data in source code. Test/mock data is acceptable only when loaded from a data source (fixtures, seed files, test APIs).
- Never deploy outside your designated region.
- Never place .md files in the root folder. All documentation goes in docs/.
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
  - *Human sign-in* is **Cognito's** job: Cognito User Pool (JWT for the CRUD path) + federated IdPs for SSO (Google native OIDC, GitHub via a small OIDC bridge since GitHub isn't OIDC, enterprise via SAML/OIDC or a WorkOS bridge). Plus a Cognito Identity Pool authenticated role (SigV4 for direct Runtime invoke) — grant it `bedrock-agentcore:InvokeAgentRuntime`. Federated SSO design: [`docs/FEDERATED_SSO.md`](docs/FEDERATED_SSO.md).
  - *Workload/outbound* auth (the agent acting on a user's behalf against external services) is **AgentCore Identity**. The two layers meet only at a `custom:*` claim carrying your canonical user id. AgentCore Identity is not your login system.
- **Security:** SOC2 foundation, TLS 1.2+, KMS on all DynamoDB tables, Secrets Manager for residual runtime secrets, IAM least-privilege per function/role. Prefer Identity/Gateway credential providers over hand-managed Secrets Manager entries for tool auth.
- **Data:** name resources on the product brand from t=0 (a rename later forces full resource recreation). No data caching unless explicitly designed.

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
├── docs/                        # All documentation (incl. AGENTCORE_FIRST.md)
├── frontend/
│   └── web/                     # React TypeScript app
│       └── src/services/        # runtimeClient.ts, useDialogueStream.ts, invokeRuntimeOnce.ts
├── tasks.md                     # Task tracking
└── utils/                       # Scripts and tools
```

## Infrastructure reference

The CRUD plane and the agent plane are **separate CDK apps** (the agent plane is provisioned via the AgentCore CDK from `agentcore.json`). Keep account-bound identifiers (Runtime ARN, Memory ID, KMS key, Cognito IDs, CloudFront IDs) in CDK context, not scattered literals — a fresh-account migration must re-point them in lockstep.

Fill in per project:

- DynamoDB tables (CRUD state only — Memory holds dialogue): [specify]
- AgentCore Runtime / Memory / Gateway IDs: [specify]
- Gateway tool targets (OpenAPI/Smithy schemas): [specify]
- API Gateway endpoints (REST, CRUD only): [specify]
- Admin APIs (require x-admin-email header): [specify]

## Tooling & deployment

Standardize on the **new CLI** `@aws/agentcore` (npm, Node 20+) with config artifact `agentcore.json`. The legacy `bedrock-agentcore-starter-toolkit` (pip; `configure`/`launch`; hidden `.bedrock_agentcore.yaml`) prints a deprecation banner — new projects don't use it. Run uv initialization before any AWS commands (see `docs/UV Setup.md`).

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
