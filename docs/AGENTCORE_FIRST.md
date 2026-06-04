# AgentCore-first: architecture, retirement ledger, and migration playbook

Consolidated lessons from building and migrating a production multi-agent app
onto Amazon Bedrock AgentCore. This is the reusable
companion to [`CLAUDE.md`](../CLAUDE.md): read it before designing the backend of
any ContextEng project that has an agent/LLM loop.

**The one-line takeaway:** if your product runs an agent loop, build it on the
AgentCore Runtime from t=0. Do **not** build it as a Lambda behind API Gateway
and migrate later. The migration is doable (one such migration took 30 commits over 11
working days, ~13K LOC of churn), but every line of it was deleting scaffolding
you should never write in the first place.

---

## 1. Why AgentCore comes first

The default AWS web-app shape — Frontend → API Gateway (REST) → Lambda → DynamoDB —
breaks the moment a request needs more than **29 seconds**, which is the API
Gateway hard sync timeout. A single role-agent turn (a Bedrock call with real
context) takes 30–90s. Teams that start on Lambda discover this on day one and
reach for the standard workaround:

> flip `turnStatus="generating"` on a DynamoDB row → async self-invoke the Lambda
> (`InvocationType=Event`) → return `202` → have the frontend poll the row every
> 1.5s until it flips to `"ready"`.

That workaround is ~700 LOC across backend and frontend, and it ships an entire
**category of bugs**: races between "the request says done" and "the state says
done" — stale reads, double-submits, `409` retry loops, frozen spinners.

AgentCore Runtime sessions run up to **8 hours** and stream progress back over
chunked-transfer SSE. The browser invokes the Runtime directly via SigV4 (no API
Gateway hop), and the "are we done yet" question becomes "watch the same stream."
The whole workaround — and the bug category — never exists.

That is the shape of the entire value proposition: **AgentCore's primitives let
you delete infrastructure scaffolding, not add features.** Argue adoption from
the retirement ledger (§4), not from the feature list.

---

## 2. The target architecture

Two compute paths from the browser. The agent path is primary; the CRUD path is a
thin supporting plane. They never call each other — they share state through
DynamoDB / AgentCore Memory.

```
Browser (React / TypeScript)
  ├─ Agent path (PRIMARY):  Cognito Identity Pool SigV4 → AgentCore Runtime
  │                           → Bedrock · Memory · Gateway · Identity
  │                         ↳ SSE: turn_started → heartbeats (2s) → *_complete
  └─ CRUD path (support):   Cognito JWT → API Gateway (REST) → Lambda → DynamoDB
```

No proxy layer fronts the Runtime. The agent path streams; the CRUD path is
request/response. Different transports, different auth flows, different timeout
characteristics — model them as two paths, never as one arrow.

### File layout to ship on day 1

```
backend/
├── runtime/                  # AgentCore-managed agent container
│   ├── app/coordinator/
│   │   ├── main.py           # BedrockAgentCoreApp entrypoint, op-dispatch
│   │   ├── runner.py         # one function per op (turn, advance, elaborate, …)
│   │   ├── llm.py            # surgical Bedrock helper over Strands BedrockModel
│   │   ├── role_agents/      # role lifecycle + dialogue I/O + prompts  (product IP)
│   │   ├── strands_agents/   # Strands Agent factory + role/aspect builders
│   │   ├── aspects/          # aspect/step specs  (product IP)
│   │   ├── memory/           # AgentCore Memory client
│   │   └── mcp_client/       # Gateway MCP client
│   └── agentcore/
│       ├── agentcore.json    # runtime + memory + credentials + gateway + evaluator
│       └── schemas/          # OpenAPI schemas for Gateway targets
├── infrastructure/           # CDK for the CRUD path + auth + storage
└── lambda/                   # CRUD only — no agent code lives here

frontend/web/src/
├── services/
│   ├── runtimeClient.ts      # AgentCore Runtime SigV4 client
│   ├── useDialogueStream.ts  # streaming hook
│   └── invokeRuntimeOnce.ts  # one-shot helper for non-streaming ops
└── api/apiSlice.ts           # RTK Query, queryFn pointing at the runtime for agent mutations
```

### Build into the runtime from t=0

1. **Uniform streaming envelope on every op.** Each op is an async generator that
   yields `*_started` immediately, `heartbeat {elapsedS}` every 2s when work
   exceeds ~5s, then a terminal `*_complete`. Even sub-second ops use the envelope,
   so the frontend handler never branches on op shape and the "frozen spinner"
   complaint never happens.
2. **Anthropic prompt-caching** (`cachePoint`) on every agent system prompt —
   30–50% prefill cost/latency cut on multi-round work. Too big to leave on the table.
3. **Speculation skip** for parallel audit+expert work: when a deterministic
   predicate guarantees the turn will force-advance, run the audit serially and
   skip the speculative expert call. Add the predicate when you add the speculation.
4. **Status-aware ops.** Bake state-machine short-circuits (e.g. a review/approval
   state that writes directly without firing the orchestrator) into the op from the
   start — one op for the frontend, status-aware on the server.
5. **OTEL on by default** (`aws-opentelemetry-distro`; entrypoint wrapped with
   `opentelemetry-instrument`). Use `logging`, never `print()`.
6. **Evaluator deployed in the same stack as the runtime**, so a prompt change can
   never ship without a regression check.

### What stays in product code (AgentCore doesn't replace this)

The orchestration doctrine (surgical Python deciding *when* to call the LLM, the
LLM adding wisdom inside bounded helpers), your domain state object (coverage,
ledger, completed/skipped work), your aspect/role/step definitions, your prompt
disciplines, and the **in-loop** auditor that gates progress (distinct from the
Evaluator, which is **post-hoc** session scoring). This is the IP — it doesn't
shrink, and it shouldn't.

### Greenfield-only wins (things a migration can't take but you can skip from t=0)

- **No dialogue table.** Memory is read+write source of truth from t=0 — no
  DynamoDB dialogue table, no dual-write phase, no eventual cutover. (Migrations
  defer this because flipping source-of-truth on live data is risky; greenfield
  has no inertia to protect.)
- **No taxonomy mirror.** One source of truth for roles/aspects, published as JSON
  (or held in Registry) — never a hand-maintained frontend copy.
- **No legacy resource names.** Brand resources correctly from t=0; a rename later
  forces full resource recreation.

---

## 3. The constraint rewrite — why CLAUDE.md rules age

The single most load-bearing change in the migration was three edits to
`CLAUDE.md`, because the original wording classified the entire target
architecture as a rule violation.

**Original (REST-only era):**
> Never add a proxy server or FastAPI layer. The architecture is Frontend → API
> Gateway (REST) → Lambda. **No exceptions.**

Taken literally, this banned *every* browser-to-AWS-service call that didn't route
through API Gateway — including `s3.upload()`, `cognito.signIn()`, and the
AgentCore Runtime SigV4 invocation the whole UX win depended on.

**Rewritten (two-path era):**
> Never add a FastAPI or Express proxy layer. CRUD path is Frontend → API Gateway
> (REST) → Lambda. The agent path may call AWS-managed serverless agent services
> directly from the frontend via Cognito Identity Pool SigV4 — that is not a proxy
> layer.

Same story for the WebSocket rule (the original conflated "push" with "WebSocket";
the Runtime's SSE stream is push but not WebSocket) and the Architecture section
(a one-arrow stack became two compute paths).

**The lesson, generalized:** a constraint that contains "no exceptions" *and* a
specific architectural literal ages badly. Rules age better when written around
**principles** ("no custom proxy layers in front of managed services") than around
**literals** ("no calls outside API Gateway"). When new infrastructure shifts the
literal, rewrite the rule to its actual intent *before* the new work starts — not
after it's been blocked. ContextEng's `CLAUDE.md` is now written this way; keep it
that way as you extend it.

---

## 4. The retirement ledger — buy-vs-build catalog

For each AgentCore primitive: the concrete code (and, more importantly, the
concrete *category of bug*) you don't write if you start with the platform
assumed. Use this to write an honest adoption memo. LOC figures are from one such
production codebase — your numbers will differ, but the *categories* generalize.

### Runtime → ~1,400 LOC + a whole bug category
Retires the 29s-timeout workaround in full: the self-invoke async pattern (~260
LOC), the `turnStatus` state machine (DynamoDB column + frontend polling loop +
transition watcher + pending-submit queue + idle poll, ~430 LOC), concurrent-
submission `409` guards, Lambda timeout/IAM tuning, and the API Gateway integration
for the multiplexed dialogue route. **Bug category retired:** all races between
"request says done" and "state says done."

### Memory → ~50 LOC today, ~3,500 LOC avoidable
Native embedding-based retrieval retires your Titan embedding wrapper. As
source-of-truth it collapses ~600 LOC of DynamoDB `query()` read shapes to
`memory.list_events()` calls and deletes the dialogue table + its KMS/IAM/backup
infra + dual-write coordination. **Bug category retired:** keeping two stores in sync.

### Gateway → ~450 LOC
Declarative OpenAPI tool targets replace hand-rolled HTTP clients (web search,
GitHub, Slack) with their secret-fetching, timeout, parsing, and fallback code,
plus all per-tool credential plumbing. **Bug category retired:** API-shape drift
between you and the upstream provider — a schema change becomes a YAML edit, not a
code-and-redeploy.

### Identity → ~600 LOC
**Scope:** AgentCore Identity is the **workload / outbound** auth layer — the agent
obtaining and using tokens to act on a user's behalf against external services, plus
inbound credential management. It replaces hand-rolled OAuth code-for-token exchange
(e.g. the app creating a repo on the user's GitHub), custom JWT signing/verify for
inbound webhooks, and HMAC signature validation.

**Boundary — what it is *not*:** AgentCore Identity is **not your human sign-in
system.** Federated *login* (Continue with Google / GitHub, enterprise SAML/OIDC) is
**Cognito's** job — Cognito User Pool federated IdPs, with a small OIDC bridge for
GitHub (which isn't an OIDC provider). The two layers meet at exactly one place: a
`custom:*` claim on the Cognito token carrying your canonical user id. Putting login
in the wrong layer is the most common identity mistake — see
[`FEDERATED_SSO.md`](FEDERATED_SSO.md), including the "three GitHubs" test (sign-in vs
act-on-repos vs public-read are three different credentials in three different layers).

**You still write** genuinely product-specific auth (e.g. an email-anchored user
upsert, an admin-class taxonomy) — that's product policy, not auth infrastructure.

### Policy → ~150 LOC
Cedar policies declaratively encode authz gates (`require_admin_class()`) and
quota counters (per-user daily call limits), enforced at the tool-call layer.
**Bug category retired:** silent drift between "what the docs say is allowed" and
"what the code actually checks" — Cedar is the single source of truth.

### Registry → ~370 LOC + a permanent bug class
Holds the canonical taxonomy and custom records (e.g. case-law) with native
semantic search, retiring the hand-maintained frontend taxonomy mirror and the
"republish on every deploy" build step. **Bug category retired:** the "we renamed
a role in the backend but forgot the frontend mirror, now half the UI shows the
old name" incident.

### Observability → ~80 LOC + a capability upgrade
OTEL auto-instrumentation attaches `otelTraceID`, `code.file.path`, token counts,
etc. to every log line for free, retiring `print()` scatter and manual token
accounting. **You gain** per-agent-step trace visualization. **Bug category
retired:** "the dialogue is slow but I can't tell where the time went."

### Evaluations → ~200 LOC avoidable
Retires a *practice*, not code: shipping prompt changes without a regression check.
The rubric lives in CFN, the LLM-as-judge runs alongside the runtime, scores are
queryable. **Debate retired:** "is the test broken or is the prompt actually worse?"

### Strands as a Lambda Layer → 100% retired
The SDK ships inside the runtime container's `pyproject.toml`. No ~80MB layer
asset, no `build.sh`, no `createLambdaWithStrands` CDK helper, no "rebuild the
layer on every SDK release" maintenance.

### Tally

| Primitive | Code retired / avoidable | Bug category retired |
|---|---|---|
| Runtime | ~1,400 LOC + frontend polling | async-vs-state races, the 29s dance |
| Memory | ~50 today / ~3,500 avoidable | dual-write coordination |
| Gateway | ~450 LOC | tool-API drift, credential plumbing |
| Identity | ~600 LOC | hand-rolled OAuth, signature bugs |
| Policy | ~150 LOC | imperative gate drift, quota bugs |
| Registry | ~370 LOC | frontend/backend taxonomy out-of-sync |
| Observability | ~80 LOC + upgrade | "where did the time go" |
| Evaluations | ~200 LOC avoidable | "is this prompt a regression" |
| Strands layer | ~100 LOC + 80MB | SDK-update maintenance |
| Frontend transport | ~400 LOC | the async-submit mental model |
| **Total** | **~3,800 LOC retired + ~4,000 avoidable** | |

---

## 5. Migration playbook (existing REST/Lambda app)

If you already have a Lambda-coordinator codebase, here's how the cutover actually
goes — and where it surprises you.

- **Plan in *call surfaces*, not Lambdas or routes.** The unit of migration is the
  `(op, frontend caller)` pair. A Lambda that multiplexes ops by request body shape
  costs `N × (port + transport + test)`, not `1×`. Name every op in the plan.
- **Phases are additive until ONE cutover phase.** Author the new path side-by-side;
  destructive deletes need the calling surface to be provably dead, and that's only
  true after the frontend fully migrates. Expect "delete X in Phase N" to really mean
  "queue X for deletion in the final cutover." Most of the LOC and all the risk land
  in that one phase.
- **Stand up the streaming envelope first, on a `ping` op.** Heartbeats,
  `turn_started` flushing, the `getReader()` pattern, and explicit break-on-terminal
  are prerequisites, not optimizations. Prove them on the smallest op before any real
  op needs them.
- **Browser validation is the smoke test.** CLI smoke tests kept passing while the
  browser path was broken. AgentCore Browser + Playwright (`browser_session` +
  `connect_over_cdp`) gives a clean Chromium with known token state — the cheapest way
  to catch frontend/backend divergence.
- **RTK Query `queryFn` is the transport-swap bridge.** Replace a mutation's `query`
  with a `queryFn` that calls `invokeRuntimeOnce(client, payload)` — same hook
  signature, same `invalidatesTags`, same return shape. No call-site changes for a
  transport change.

### Gotchas that ate the most time (all surfaced as "the dialogue hangs at round N")

1. **`asyncio.run()` raises inside the Runtime event loop.** The entrypoint already
   runs a loop. `nest_asyncio` breaks uvicorn. Fix: drive Strands' async stream inside
   a `concurrent.futures.ThreadPoolExecutor` with its own loop.
2. **30s AWS SDK read timeout** on the browser→Runtime call. Fix:
   `FetchHttpHandler({ requestTimeout: 300_000 })`.
3. **Trailing post-JSON commentary** from the model on long contexts ("Extra data:
   line 1 column N"). Fix: `json.JSONDecoder().raw_decode(stripped)`, not `json.loads()`.
4. **Web `ReadableStream` `for await…of`** only works in Chrome 124+. Fix: explicit
   `reader.getReader()` loop.
5. **Stream EOF doesn't propagate** cleanly through CloudFront + Runtime proxies. Fix:
   explicit `break` on `turn_complete`/`error` in the client.

### AWS / AgentCore operational gotchas

- **Keep `agentcore deploy` healthy.** A CDKToolkit stack stuck in
  `REVIEW_IN_PROGRESS` fails the bootstrap pre-check; document a raw `cdk deploy`
  fallback, but fix the bootstrap rather than living on the workaround.
- **Deploy context flags are load-bearing.** Omitting `--context domainNames=… --context
  certificateArn=…` silently drops custom-domain CORS and flips `FRONTEND_URL`s to the
  CloudFront domain. Diff the synth before every deploy.
- **`aws/spans` is AWS-reserved** and auto-creates when OTEL spans first land; you
  can't pre-create it. If the platform pre-wires its own TracerProvider and bypasses
  ADOT's signed exporter, spans 400 — `OTEL_TRACES_EXPORTER=none` silences the spam
  while spans still flow as CloudWatch log events.
- **Gateway authorizer is immutable post-create** — changing it recreates the Gateway
  and re-attaches all targets. Don't ship `authorizerType: NONE` to anything external.
- **CodeZip silently drops a directory** whose name collides with a top-level package
  in the dependency tree (e.g. a dir named `agentcore/`). Rename it (`app_memory/`).
- **Evaluator quirks:** `description` max 200 chars; `instructions` treats `{…}` as
  placeholder syntax with an AWS allowlist — output schemas must be line-formatted text,
  not JSON examples.

---

## 6. Writing the adoption memo

1. **Argue from the retirement ledger, not features.** "Memory is GA" is a feature;
   "we don't build dual-write coordination" is the operative value. Make the case in
   code-you-don't-write.
2. **Count bug categories, not just lines.** The 29s dance was ~260 LOC, but its
   absence retires an entire class of races that would live in your tracker forever.
3. **Draw the product/infrastructure line first.** Everything in "what stays in
   product code" is yours regardless; everything in the retirement ledger is what you'd
   pay AgentCore to not write. That line tells you the actual trade.
4. **Adopt incrementally if you must — but plan the one cutover phase.** Additive,
   side-by-side, then a single phase where the old paths come out together.
5. **The platform's opinions become your design constraints.** You write Cedar
   policies, OpenAPI schemas, JSON Schema records, and LLM-as-judge rubrics instead of
   imperative code. If your team is comfortable declarative-first, that's a feature; if
   not, plan the learning curve.

---

*Source: a production Lambda-coordinator → AgentCore Runtime migration (2026). The
product-specific after-action lived in that repo and was consolidated here so future
ContextEng projects inherit the lessons instead of relearning them.*
