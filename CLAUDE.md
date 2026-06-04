# CLAUDE.md

> Template for AI-DLC projects seeded from ContextEng. The architecture is
> **AgentCore-first**: if your product has an agent/LLM loop, that loop lives in
> the AgentCore Runtime from day one — not in a Lambda behind API Gateway. The
> full rationale, the buy-vs-build retirement ledger, and the migration gotchas
> are in [`docs/AGENTCORE_FIRST.md`](docs/AGENTCORE_FIRST.md). Read it before you
> design the backend.

## Constraints

Never do these things:

- Never propose or implement workarounds, shortcuts, or stopgap fixes that introduce tech debt. Diagnose the root cause and design a lasting solution. When a lasting fix is not feasible right now (cost, scope, upstream dependency), surface that constraint explicitly so the trade-off is a deliberate decision — not a quietly-shipped band-aid.
- **Agent code lives in the AgentCore Runtime, not in Lambda.** The agent/LLM path is Frontend → AgentCore Runtime (Strands container, direct SigV4) → Bedrock + Memory + Gateway. Do not build agent orchestration as a Lambda behind API Gateway: the 29-second API Gateway sync timeout forces a `turnStatus="generating"` self-invoke + frontend-polling workaround that AgentCore exists to delete.
- Never add a FastAPI or Express **proxy layer**. CRUD path is Frontend → API Gateway (REST) → Lambda. The agent path calls AWS-managed serverless agent services (AgentCore Runtime) directly from the frontend via Cognito Identity Pool SigV4 — that is *not* a proxy layer. Two compute paths, no custom proxy fleet. (This rule is written around the principle — "no custom proxy layers in front of managed services" — not the literal "everything goes through API Gateway." A rule written around a literal ages badly; see `docs/AGENTCORE_FIRST.md` §"The constraint rewrite.")
- Never ship Strands (or any agent SDK) as a Lambda Layer. It ships inside the Runtime container's own `pyproject.toml`. SDK bumps are a one-line edit + redeploy, no layer rebuild.
- Never LLM-drive routing or orchestration. Deterministic Python decides *when* to call the model; the LLM adds wisdom inside clearly-bounded helpers. The orchestrator is plumbing, not an agent.
- Never hardcode mock data in source code. Test/mock data is acceptable only when loaded from a data source (fixtures, seed files, test APIs).
- Never deploy outside your designated region.
- Never place .md files in the root folder. All documentation goes in docs/.
- Never commit code unless the user explicitly asks.
- Never add code comments unless the user explicitly asks.
- Never call python or pip directly. Use `uv run` for execution, `uv pip` or `uv add` for package management. uv is a prerequisite.

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

- Backend: Python 3.12+ with strict typing
- Frontend: TypeScript with strict typing
- Security: client-side encryption for sensitive data, all API keys in .gitignore
- Infrastructure: CDK/CloudFormation only, templates in backend/infrastructure/
- Observability: use `logging.getLogger(__name__)`, never `print()` — OTEL auto-instrumentation attaches trace context to every log line.

## Architecture — AgentCore first

Two compute paths from the browser. The **agent path is primary**; the CRUD path is a thin supporting plane. They never call each other — they share state through DynamoDB / AgentCore Memory.

```
Browser (React / TypeScript)
  ├─ Agent path (PRIMARY):  Cognito Identity Pool SigV4 → AgentCore Runtime (Strands container)
  │                           → Bedrock (models) · Memory (dialogue) · Gateway (MCP tools) · Identity (outbound auth)
  │                         ↳ chunked-transfer SSE: turn_started → heartbeats (2s) → *_complete
  └─ CRUD path (support):   Cognito JWT → API Gateway (REST) → Lambda → DynamoDB
```

No API Gateway hop on the agent path — the browser invokes the Runtime directly with credentials vended by the Cognito Identity Pool authenticated role.

**Why AgentCore comes first.** Building the agent loop as a Lambda behind API Gateway hits the 29-second sync timeout and forces a self-invoke + `turnStatus` polling state machine (~700 LOC of plumbing across backend and frontend, plus a permanent class of async-vs-state races). AgentCore Runtime sessions run up to 8 hours and stream progress, deleting that entire category. Design for the Runtime from t=0; do not build the Lambda path first and migrate. (One such migration cost 30 commits over 11 working days and ~13K LOC of churn. See `docs/AGENTCORE_FIRST.md`.)

**AgentCore primitives** — adopt the ones your product needs; each is infrastructure you don't write, deploy, monitor, or debug:

| Primitive | Replaces | What you write instead |
|---|---|---|
| **Runtime** | Self-invoke async pattern, `turnStatus` state machine, 29s-timeout dance | An op-dispatch entrypoint + a streaming envelope |
| **Memory** | DynamoDB dialogue table, dual-write coordination, embedding pipeline | `memory.list_events()` / `create_event()` |
| **Gateway** | Hand-rolled HTTP clients + per-tool credential plumbing | OpenAPI schema per tool target |
| **Identity** *(workload/outbound only — NOT human sign-in)* | Hand-rolled outbound OAuth, JWT signing, signature validation | A declared credential provider |
| **Policy** | Imperative `require_admin_class()` gates, quota counters | Cedar policies |
| **Observability** | `print()` + Athena heroics, manual token accounting | `logging` + OTEL spans (free) |
| **Evaluator** | Ad-hoc prompt smoke tests | An LLM-as-judge rubric in CFN |

**What stays in product code** — AgentCore has no opinion about these, and that's correct: the orchestration doctrine (surgical Python deciding *when* to call the LLM), your domain state object (coverage, ledger, completed/skipped work), your aspect/role/task definitions, your prompt disciplines, and the in-loop auditor that gates progress. That is the IP. Everything in the table above is infrastructure; everything here is the product.

### Build into the runtime from t=0

- **Uniform streaming envelope on every op** (async generator: `*_started` immediately → `heartbeat {elapsedS}` every 2s when work exceeds ~5s → terminal `*_complete`). The frontend handler never branches on op shape, and the "frozen spinner" complaint never happens.
- **Anthropic prompt-caching** (`cachePoint`) on every agent system prompt — 30-50% prefill cost/latency cut on multi-round work.
- **OTEL on by default** (`aws-opentelemetry-distro` in runtime deps; entrypoint wrapped with `opentelemetry-instrument`).
- **Worker-thread executor** for Strands async streams: the Runtime entrypoint already runs an event loop, so `asyncio.run()` raises `RuntimeError`. Drive the stream inside a `concurrent.futures.ThreadPoolExecutor`, not `nest_asyncio`.
- **Evaluator deployed in the same stack as the runtime**, so a prompt can never ship without a regression check.
- **Frontend transport**: AWS SDK `FetchHttpHandler({ requestTimeout: 300_000 })` (the 30s default kills long turns); a `getReader()` loop (not `for await…of`, patchy pre-Chrome 124); explicit `break` on the terminal event (EOF doesn't propagate cleanly through CloudFront + Runtime proxies). Expose agent mutations through RTK Query `queryFn → invokeRuntimeOnce(...)` so transport changes need zero call-site edits.

## Stack / Auth / Security

- **Region:** one region only (pick yours); us-east-1 is the exception only for a CloudFront ACM cert.
- **Auth — two layers, don't conflate them:**
  - *Human sign-in* is **Cognito's** job: Cognito User Pool (JWT for the CRUD path) + federated IdPs for SSO (Google native OIDC, GitHub via a small OIDC bridge since GitHub isn't OIDC, enterprise via SAML/OIDC or a WorkOS bridge). Plus a Cognito Identity Pool authenticated role (SigV4 for direct Runtime invoke) — grant it `bedrock-agentcore:InvokeAgentRuntime`. Federated SSO design: [`docs/FEDERATED_SSO.md`](docs/FEDERATED_SSO.md).
  - *Workload/outbound* auth (the agent acting on a user's behalf against external services) is **AgentCore Identity**. These meet only at a `custom:*` claim carrying your canonical user id. AgentCore Identity is not your login system.
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
│   │   │   ├── llm.py           # surgical Bedrock helper over Strands BedrockModel
│   │   │   ├── role_agents/     # role lifecycle + dialogue I/O + prompts (product IP)
│   │   │   ├── strands_agents/  # Strands Agent factory + role/aspect builders
│   │   │   ├── aspects/         # aspect/step specs (product IP)
│   │   │   ├── memory/          # AgentCore Memory client (avoid dir names that collide
│   │   │   │                    #   with top-level dependency packages — CodeZip drops them)
│   │   │   └── mcp_client/      # Gateway MCP client
│   │   └── agentcore/
│   │       ├── agentcore.json   # runtime + memory + credentials + gateway + evaluator spec
│   │       └── schemas/         # OpenAPI schemas for Gateway tool targets
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
- Gateway tool targets (OpenAPI schemas): [specify]
- API Gateway endpoints (REST, CRUD only): [specify]
- Admin APIs (require x-admin-email header): [specify]

## AWS operations

Run uv initialization before any AWS commands. See `docs/UV Setup.md`.

Deploy: the agent plane deploys via `agentcore deploy` (or the AgentCore CDK directly when bootstrap is unhealthy — keep the raw `cdk deploy` fallback documented). The CRUD plane deploys via `npx cdk deploy --all` with any domain/cert context flags (those flags are load-bearing — omitting them silently drops custom-domain CORS).
