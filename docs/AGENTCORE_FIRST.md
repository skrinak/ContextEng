# AgentCore-first: architecture, primitive ledger, and the decisions that matter

The reusable architecture companion to [`CLAUDE.md`](../CLAUDE.md). Read it before
you design the backend of any ContextEng project that has an agent or LLM loop.

**The one-line takeaway:** if your product runs an agent loop, run that loop on
**Amazon Bedrock AgentCore** from t=0 — not as a Lambda behind API Gateway you
migrate later. AgentCore's whole value is *infrastructure you delete*, not
features you add: managed sessions, streaming, memory, tool gateways, identity,
policy, and observability that you would otherwise hand-roll, debug, and carry
forever.

> **Status freshness.** AgentCore is moving fast. This doc reflects the platform
> as of **mid-2026**. Where a fact is version-sensitive (GA vs preview, CLI verb
> names, config filenames) it is marked. Always confirm against the live
> [AgentCore developer guide](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/)
> before treating any specific identifier as load-bearing.

---

## 1. Why AgentCore comes first

The default AWS web-app shape — Frontend → API Gateway (REST) → Lambda → DynamoDB —
breaks the moment a request needs more than **29 seconds**, the API Gateway hard
sync timeout. A single agent turn (a model call with real context, possibly tool
calls) routinely takes 30–120s. Teams that start on Lambda hit this on day one
and reach for the standard workaround:

> flip `turnStatus="generating"` on a DynamoDB row → async self-invoke the Lambda
> (`InvocationType=Event`) → return `202` → have the frontend poll the row every
> ~1.5s until it flips to `"ready"`.

That workaround is hundreds of lines across backend and frontend, and it ships an
entire **category of bugs**: races between "the request says done" and "the state
says done" — stale reads, double-submits, `409` retry loops, frozen spinners.

AgentCore **Runtime** sessions run up to **8 hours**, stream progress back over
chunked-transfer SSE (and bidirectional WebSocket), and isolate each session in
its own microVM. The browser invokes the Runtime directly via SigV4 — no API
Gateway hop — and "are we done yet?" becomes "watch the same stream." The whole
workaround, and its bug category, never exists.

That is the shape of the entire value proposition: **AgentCore's primitives let
you delete infrastructure scaffolding.** Argue adoption from the retirement
ledger (§6), not from a feature list.

---

## 2. Deterministic-first: tokenomics is the real gate

AgentCore-first is **not agent-everything.** The most expensive mistake after
"build the agent on Lambda" is "route work through the model that plain code should
have computed." The model is the slowest, costliest, least reproducible component
in your stack — reach for it **last**, not first. AgentCore is where the agent loop
*lives*; it is not where every feature *starts*.

**Why tokenomics is the gate, not a nicety.** Token cost is the single biggest
reason agentic prototypes never reach production:

- Anthropic's own measurement: agents use ~4× the tokens of a chat turn, and
  **multi-agent systems use ~15× more tokens than chat** — and **token usage by
  itself explains ~80% of the variance** in system performance. Multi-agent
  architectures are viable only when "the value of the task is high enough to pay
  for the increased performance."
  ([Anthropic — multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system))
- Cost compounds super-linearly: the full history (prompts, tool calls, tool
  outputs) is re-sent every turn, so a 4-turn loop bills ~10× the first turn's
  tokens, not 4×; real agent loops routinely cost **5–10× the naïve estimate.**
- Gartner projects **>40% of agentic AI projects will be canceled by end of 2027**,
  with escalating cost named a primary driver. What kills agents in production is
  the bill, not model quality.

**The discipline (Anthropic's "[Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)," distilled):**
"find the simplest solution possible, and only increase complexity when needed."
Most problems are *workflows* — LLMs and tools orchestrated through **predefined
code paths** — not *agents* that dynamically direct their own control flow.
"Optimizing single LLM calls with retrieval and in-context examples is usually
enough." Reserve a true agent loop for tasks you genuinely cannot hardcode but can
still verify.

This is exactly ContextEng's orchestration doctrine (`CLAUDE.md`): **deterministic
Python decides *when* to call the model; the model adds wisdom only inside bounded
helpers.** A cache hit, a DynamoDB lookup, a regex, a SQL query, or a Cedar policy
returns a deterministic answer in milliseconds at near-zero marginal cost and 100%
reproducibility. Paying frontier per-token rates to *generate* an answer you could
have *computed* is the core anti-pattern. **Compute the answer when you can;
generate it only when you must.**

### The two paths live in harmony — that's why there are two

The CRUD path (Frontend → API Gateway → Lambda → DynamoDB) is **not** the legacy
plane the agent path replaces. It is the **deterministic-first plane** — often the
fastest, cheapest, most reliable way to ship a result — and API Gateway is
frequently the quickest route to a known, deterministic answer. The agent path is
the *expensive exception* reserved for open-ended judgment. The §3 architecture
draws two paths **precisely because most work belongs on the cheap one.** When a
requirement arrives, the order of preference is:

1. **Can plain code compute it?** (lookup, rule, arithmetic, validation, join) →
   CRUD path, no model call.
2. **Does it need judgment in one bounded spot?** → a single structured /
   function-calling model call inside deterministic code (router, classifier,
   extractor, judge), still orchestrated by Python.
3. **Is the path genuinely un-hardcodable but verifiable?** → a real agent loop on
   the Runtime — now you pay the 15× and it's worth it.

"AgentCore from t=0" means *when you reach rung 3, it already runs on AgentCore.*
It does **not** mean starting every feature at rung 3.

### Make the agent path affordable once you reach it

When the work genuinely needs the model, these are table stakes for production
economics — and most map to AgentCore primitives you're already adopting:

- **Model cascade / routing.** Cheapest capable model first (Haiku-tier), escalate
  to Sonnet/Opus only on low confidence (FrugalGPT-style cascades report up to
  ~98% cost cuts at matched accuracy). Frontier input is ~5× small-model input, and
  output ~5× input across tiers — so verbose generation, not prompt size, usually
  dominates. Cap `max_tokens`; prompt for terseness.
- **Prompt caching** (`cachePoint`): ~90% off cached-prefix reads, break-even at two
  requests (5-min TTL). A timestamp or UUID in the system prompt silently
  invalidates the whole cache — keep the cached prefix byte-stable.
- **Memory + retrieval over long context.** Retrieve the few relevant facts
  (AgentCore Memory) instead of re-sending a growing transcript every turn.
- **Bounded loops.** Hard max-iteration stopping conditions; reflection/retry loops
  are the quietest budget sink.
- **Batch API** (50% off) for anything not latency-sensitive; **semantic caching**
  of results for repeat-shaped queries.
- **Measure cost-per-resolved-task, not cost-per-token.** Token price is the wrong
  number to optimize in isolation; the unit of business value is the resolved task.

> The retirement ledger (§6) and tokenomics point the same way: adopt AgentCore
> because it deletes infrastructure *and* because its primitives (Memory, prompt
> caching, Policy, model routing) are where cost control actually lives. But the
> cheapest token is the one you never spend — **deterministic-first, first.**

---

## 3. The target architecture

Two compute paths from the browser. The **agent path is primary** — meaning it is
the architecturally distinctive plane this whole doc is about, *not* that most
requests flow through it. By volume, the deterministic CRUD path should carry the
majority of work (§2); the agent path is the expensive exception you reach for only
when the model genuinely adds wisdom. They never call each other — they share state
through DynamoDB and AgentCore Memory.

```
Browser (React / TypeScript)
  ├─ Agent path (PRIMARY):  Cognito Identity Pool SigV4 → AgentCore Runtime (or Harness)
  │                           → Bedrock · Memory · Gateway · Identity · Policy · Observability
  │                         ↳ SSE / WebSocket: *_started → heartbeats → *_complete
  └─ CRUD path (support):   Cognito JWT → API Gateway (REST) → Lambda → DynamoDB
```

No proxy layer fronts the Runtime. The agent path streams; the CRUD path is
request/response. Different transports, different auth flows, different timeout
characteristics — model them as two paths, never as one arrow.

> **The principle, not the literal.** "No proxy layer" means *no custom proxy
> fleet in front of managed services*. A direct browser→Runtime SigV4 call is not
> a proxy. A direct `s3.upload()` or `cognito.signIn()` is not a proxy. See §5 for
> why writing the rule as a literal ("everything goes through API Gateway") ages
> badly and how to write it around the principle instead.

### File layout to ship on day 1

```
backend/
├── runtime/                  # AgentCore-managed agent container (the agent path)
│   ├── app/coordinator/
│   │   ├── main.py           # BedrockAgentCoreApp entrypoint, op-dispatch
│   │   ├── runner.py         # one function per op (turn, advance, elaborate, …)
│   │   ├── llm.py            # surgical model helper over the framework's model class
│   │   ├── domain/           # your orchestration doctrine + domain state  (product IP)
│   │   ├── agents/           # agent/tool factory (Strands / LangGraph / custom)
│   │   ├── memory/           # AgentCore Memory wiring (avoid dir names that collide
│   │   │                     #   with top-level dependency packages — CodeZip drops them)
│   │   └── mcp_client/       # Gateway MCP client
│   └── agentcore/
│       ├── agentcore.json    # new-CLI config: runtime + memory + gateway + identity + evaluator
│       └── schemas/          # OpenAPI / Smithy schemas for Gateway targets
├── infrastructure/           # CDK for the CRUD path + auth + storage
└── lambda/                   # CRUD only — no agent code lives here

frontend/web/src/
├── services/
│   ├── runtimeClient.ts      # AgentCore Runtime SigV4 client (InvokeAgentRuntime)
│   ├── useDialogueStream.ts  # streaming hook (getReader loop)
│   └── invokeRuntimeOnce.ts  # one-shot helper for non-streaming ops
└── api/apiSlice.ts           # RTK Query, queryFn pointing at the runtime for agent mutations
```

---

## 4. The decision that comes before everything: **Harness vs. Runtime**

AgentCore now offers two ways to run an agent loop. Choosing between them is the
first architectural decision, and it is a genuine fork — pick deliberately.

| | **Runtime** (code-based loop) | **Harness** (managed loop) |
|---|---|---|
| You write | The orchestration loop in Python (an entrypoint + your dispatch) | **Config** — model + system prompt + tools + skills + memory; AgentCore runs the loop |
| Invoke API | `InvokeAgentRuntime` (SigV4) | `InvokeHarness` (also available as a Step Functions state) |
| Framework | Strands, LangGraph, CrewAI, LlamaIndex, Google ADK, OpenAI Agents SDK, or raw custom — your choice, inside your code | Strands-powered under the hood; you don't see it |
| Control | Total — deterministic Python decides *when* to call the model | The platform decides; you steer with config, skills, and tool/policy boundaries |
| Model swap | Your code | Switch providers (Bedrock / OpenAI / Gemini / any LiteLLM) **mid-session** without losing context |
| Versioning | You manage endpoints/versions | Immutable versions + named endpoints + instant rollback, built in |
| Status | **GA** (since Oct 2025) | **GA** (since ~Apr 2026) |

**ContextEng's doctrine is the Runtime path.** The core `CLAUDE.md` rule —
*"Never LLM-drive routing or orchestration; deterministic Python decides when to
call the model, the LLM adds wisdom inside bounded helpers"* — is fundamentally a
**code-based-loop** choice. It buys you: an auditable state object, in-loop gating,
prompt-caching control, speculation skips, and status-aware short-circuits that a
managed loop will not give you. For a product whose IP *is* the orchestration
doctrine, write the loop.

**When Harness is the right call instead:** the agent loop is conventional
(retrieve → reason → call tools → answer), you want a production-grade agent in
hours not weeks, you need mid-session model switching or fast A/B-by-config, and
the orchestration is not itself the product. Harness can also `export to Strands
code` later — start managed, drop to Runtime when you outgrow the config surface.

> Harness is built **on** Runtime — each harness session is a stateful isolated
> microVM with its own filesystem and shell. The two are not separate products;
> Harness is the no-code front of the same engine. There's a dedicated
> `harness-vs-runtime` page in the devguide; read it before committing.

If you choose Runtime, everything in §4.1 applies. If you choose Harness, most of
it is handled for you — you instead invest in the config, the skills you attach,
the Gateway tool targets, and the Policy boundary.

### 4.1 Build into the Runtime from t=0

The SDK already does more than the old guidance assumed. The entrypoint contract
is genuinely three lines — `BedrockAgentCoreApp()` + `@app.entrypoint` + `app.run()`
— and the SDK owns the HTTP server on `:8080`, SSE framing, the `/ping` health
route, and a **dedicated worker event loop on a background thread** (so a blocking
handler can't starve liveness). Don't re-teach those as things you write.

```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp
app = BedrockAgentCoreApp()

@app.entrypoint
async def invoke(payload, context):           # async generator → auto text/event-stream
    agent = get_or_create_agent(context.session_id)
    async for event in agent.stream_async(payload.get("prompt", "")):
        if isinstance(event.get("data"), str):
            yield event["data"]

if __name__ == "__main__":
    app.run()
```

What you *do* own, and should build in from t=0:

1. **Uniform streaming envelope on every op.** Each op yields `*_started`
   immediately, a `heartbeat {elapsedS}` every ~2s when work exceeds ~5s, then a
   terminal `*_complete`. Even sub-second ops use the envelope, so the frontend
   handler never branches on op shape and "frozen spinner" never happens.
2. **Anthropic prompt-caching** (`cachePoint`) on every agent system prompt —
   a 30–50% prefill cost/latency cut on multi-round work. Too big to leave on the
   table. (Confirm the current model and SDK both honor the cache point.)
3. **Status-aware ops.** Bake state-machine short-circuits (e.g. a review/approval
   state that writes directly without firing the orchestrator) into the op from
   the start — one op for the frontend, status-aware on the server.
4. **Observability on by default.** `aws-opentelemetry-distro` in deps; the
   generated Dockerfile wraps the entrypoint with `opentelemetry-instrument`;
   `AGENT_OBSERVABILITY_ENABLED=true`. Use `logging`, never `print()`. (A single
   `--disable-otel` flag turns it off; default is on — leave it on.)
5. **Evaluator wired into the same deploy** (preview), so a prompt change can't
   ship without a regression check.

### 4.2 What stays in product code (AgentCore has no opinion about these — correctly)

The orchestration doctrine (surgical Python deciding *when* to call the model, the
model adding wisdom inside bounded helpers), your domain state object (coverage,
ledger, completed/skipped work), your task/role/step definitions if you have them,
your prompt disciplines, and the **in-loop** auditor that gates progress (distinct
from the post-hoc Evaluator). **This is the IP.** It doesn't shrink, and it
shouldn't. Everything in §6 is infrastructure you rent; everything here is the
product you build.

### 4.3 Greenfield-only wins (a migration can't take these — you can skip them from t=0)

- **No dialogue table.** Memory is read+write source of truth from day one — no
  DynamoDB dialogue table, no dual-write phase, no eventual cutover.
- **No taxonomy mirror.** One source of truth for your domain taxonomy, published
  as JSON or served from the runtime — never a hand-maintained frontend copy.
- **No legacy resource names.** Brand resources correctly from t=0; a rename later
  forces full resource recreation.

---

## 5. The constraint rewrite — why CLAUDE.md rules age

The single most load-bearing lesson from migrating a real app was that the
original `CLAUDE.md` wording classified the entire target architecture as a rule
violation.

**Original (REST-only era):**
> Never add a proxy server or FastAPI layer. The architecture is Frontend → API
> Gateway (REST) → Lambda. **No exceptions.**

Taken literally, this banned *every* browser-to-AWS-service call that didn't route
through API Gateway — including `s3.upload()`, `cognito.signIn()`, and the
AgentCore Runtime SigV4 invocation the whole UX win depends on.

**Rewritten (two-path era):**
> Never add a FastAPI or Express proxy layer. CRUD path is Frontend → API Gateway
> (REST) → Lambda. The agent path may call AWS-managed serverless agent services
> directly from the frontend via Cognito Identity Pool SigV4 — that is not a proxy
> layer.

**The lesson, generalized:** a constraint that contains "no exceptions" *and* a
specific architectural literal ages badly. Rules age better when written around
**principles** ("no custom proxy layers in front of managed services") than around
**literals** ("no calls outside API Gateway"). When new infrastructure shifts the
literal, rewrite the rule to its actual intent *before* the new work starts — not
after it's been blocked. ContextEng's `CLAUDE.md` is now written this way; keep it
that way as you extend it.

---

## 6. The primitive ledger — buy-vs-build catalog

For each AgentCore primitive: what it is, its status, the developer surface you
actually touch, and — most importantly — the concrete *category of bug* you don't
own if you start on the platform. Use this to write an honest adoption memo. LOC
figures are illustrative from one production codebase; your numbers will differ,
but the *categories* generalize.

### Runtime — GA · retires the 29s dance + a whole bug category
Serverless microVM host for any agent or MCP/A2A tool; framework- and
model-agnostic; up to 8-hour sessions, 100 MB payloads, persistent filesystem
across stop/resume, SSE **and** bidirectional WebSocket streaming. Invoke via
`InvokeAgentRuntime` (SigV4), keyed on the Runtime ARN, with named endpoints and
immutable versions. **Retires:** the self-invoke async pattern, the `turnStatus`
state machine, concurrent-submission `409` guards, Lambda timeout/IAM tuning, and
the API Gateway integration for the dialogue route. **Bug category retired:** all
races between "request says done" and "state says done."

### Harness — GA · retires the orchestration-infra layer entirely
A managed agent loop: declare model + prompt + tools + skills + memory in config,
invoke with `InvokeHarness`, and AgentCore runs the loop, versioning, endpoints,
and rollback. Mid-session model switching, attachable AWS Skills, A/B via
Evaluations. **Retires:** writing the loop, model-swap plumbing, version/endpoint
management. **Trade-off:** you give up deterministic control of *when* the model
is called — see §4 before adopting.

### Memory — GA · ~3,500 LOC avoidable
Managed short-term (turn-by-turn within a session) + long-term (cross-session
extracted facts/preferences/summaries) memory. Prefer the **native framework
integration** — e.g. wire it as a Strands `session_manager` so dialogue
persistence and long-term retrieval happen automatically per turn:

```python
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

session_manager = AgentCoreMemorySessionManager(
    AgentCoreMemoryConfig(
        memory_id=MEMORY_ID, session_id=session_id, actor_id=user_id,
        retrieval_config={f"/facts/{user_id}/": RetrievalConfig(top_k=10, relevance_score=0.4)},
    ), REGION)
agent = Agent(model=load_model(), session_manager=session_manager, tools=[...])
```

The low-level `MemoryClient` (`create_event`, `get_last_k_turns`,
`retrieve_memories`, with `semanticMemoryStrategy` / `userPreferenceStrategy` /
`summaryMemoryStrategy`) is the escape hatch when you need manual control.
**Retires:** the DynamoDB dialogue table + its KMS/IAM/backup infra, the embedding
pipeline, and dual-write coordination. **Bug category retired:** keeping two
stores in sync.

### Gateway — GA · ~450 LOC
A fully-managed AI gateway: single secure entry point for agentic traffic. Declare
tool targets from **OpenAPI, Smithy, or Lambda**; Gateway converts them into MCP
tools, handles ingress + egress auth (OAuth flows, token refresh, credential
injection), and offers **semantic tool selection** across thousands of tools to
keep the prompt small. The agent consumes them over MCP (`streamablehttp_client` →
`MCPClient.list_tools_sync()` → framework-native tool objects). **Retires:**
hand-rolled HTTP clients + per-tool secret/timeout/parse/fallback code +
credential plumbing. **Bug category retired:** API-shape drift — a schema change
is a target-config edit, not a code-and-redeploy.

### Identity — GA · ~600 LOC
The **workload / outbound** auth layer: the agent obtaining and using tokens to act
on a user's behalf against external services, plus inbound caller verification.
Create credential providers (`create_oauth2_credential_provider`,
`create_api_key_credential_provider`); consume with decorators
(`@requires_access_token(provider_name=…, auth_flow="M2M"|"USER_FEDERATION"|"ON_BEHALF_OF_TOKEN_EXCHANGE", …)`
injecting the token as a kwarg; `@requires_api_key`). Secure vault storage for
refresh tokens; works with Cognito, Okta, Entra ID, Auth0.

> **Boundary — what it is *not*:** AgentCore Identity is **not your human sign-in
> system.** Federated *login* (Continue with Google / GitHub, enterprise
> SAML/OIDC) is **Cognito's** job. The two layers meet at exactly one place: a
> `custom:*` claim on the Cognito token carrying your canonical user id. Putting
> login in the wrong layer is the most common identity mistake — see
> [`FEDERATED_SSO.md`](FEDERATED_SSO.md) and its "three GitHubs" test (sign-in vs
> act-on-repos vs public-read are three credentials in three layers).

**Retires:** hand-rolled OAuth code-for-token exchange, inbound JWT signing/verify,
HMAC signature validation. **You still write** genuinely product-specific auth
(email-anchored user upsert, an admin-class taxonomy) — that's product policy.

### Policy — GA (~early 2026) · ~150 LOC
A deterministic guardrail layer enforced **at the Gateway boundary**: create a
policy engine, store policies, associate with Gateways, and every tool call is
checked before execution. Author in **Cedar** *or* in **natural language** (English
→ candidate Cedar, validated against the tool schema and checked by automated
reasoning for overly-permissive / unsatisfiable rules). Fine-grained on user
identity + tool input params; decisions logged to CloudWatch. **Retires:**
imperative in-code gates (`require_admin_class()`) and quota counters. **Bug
category retired:** drift between "what the docs say is allowed" and "what the code
checks." **Caveat:** Policy only governs tools that route through Gateway.

### Observability — GA · ~80 LOC + a capability upgrade
Standardized OpenTelemetry telemetry into CloudWatch: built-in metrics (session
count, latency, duration, token usage, error rates) for agents/gateway/memory, a
console dashboard with per-step trace visualizations, and custom spans via plain
OTEL. Enabled by three things, all default-on: the `aws-opentelemetry-distro` dep,
the `opentelemetry-instrument` CMD wrap, and `AGENT_OBSERVABILITY_ENABLED=true`.
Session correlation via OTEL baggage (`session.id`) auto-attaches to every log line
and span. **Retires:** `print()` + Athena heroics, manual token accounting. **Bug
category retired:** "the dialogue is slow but I can't tell where the time went."

### Code Interpreter — GA · self-managed sandbox infra retired
An isolated sandbox for agents to write/execute/debug code (Python, JavaScript,
TypeScript), ≤100 MB inline upload / ≤5 GB via S3, default 15-min exec extendable
to 8 hr, internet access, CloudTrail-logged. Idiom: the `code_session` context
manager, or the framework tool wrapper (e.g. Strands `AgentCoreCodeInterpreter`).
**Retires:** any self-managed jailing/sandbox infra for arbitrary code execution.

### Browser Tool — GA · self-hosted headless-browser fleet retired
A managed, isolated cloud browser (`aws.browser.v1` or a custom resource): start a
session (default 15-min TTL, max 8 hr), get a SigV4-signed CDP WebSocket endpoint
(`browser_session(...).generate_ws_headers()`) and drive it with Playwright, Nova
Act, BrowserUse, or Strands; session recording → S3, replay + CloudTrail. **Doubles
as the cleanest frontend smoke test**: a clean Chromium with known token state is
the cheapest way to catch frontend/backend divergence that CLI smoke tests miss.

### Registry — Preview · org-level discovery & governance
**Note:** this is *not* a product-data store. AgentCore Registry is a managed,
org-wide **catalog** to publish, govern, and discover **MCP servers, agents, agent
skills, tools, and custom resources** — a discovery service, not a runtime. Two
resource types (Registries and Registry records, the latter validated against
protocol schemas), an admin → publisher → curator → consumer approval workflow,
**hybrid (semantic + keyword) search**, access via AWS SDK/CLI **or** a remote MCP
endpoint any MCP client (or AI agent) can call. **Solves:** tool/agent sprawl —
teams rebuilding MCP servers and agents because they can't find the ones that
already exist. Adopt it at org scale, not for a single product's taxonomy.

### Evaluations — Preview · ~200 LOC + a practice
LLM-as-a-Judge scoring over sessions/traces/spans. Built-in evaluators
(`Builtin.Helpfulness`, …) plus custom ones; modes include online, on-demand,
batch, dataset, and simulation; ingests Strands and LangGraph traces instrumented
with OTel/OpenInference; results land in Observability. **Retires a *practice***:
shipping prompt changes without a regression check. **Debate retired:** "is the
test broken or is the prompt actually worse?"

### Optimization — Preview · continuous prompt/tool improvement
Points at your traces and generates system-prompt and tool-description
recommendations, packaged as versioned config bundles and validated by A/B traffic
splitting through Gateway. Builds on Evaluations. Adopt once you have trace volume
worth mining.

### Payments — emerging · agent-initiated transactions
Managed microtransactions so an agent can pay for paid APIs / MCP / content via the
**x402** protocol, with wallet integration and spending limits. Relevant only if
your agents transact; otherwise skip. Confirm current status before designing on it.

### Tally (illustrative)

| Primitive | Status | Code retired / avoidable | Bug category retired |
|---|---|---|---|
| Runtime | GA | ~1,400 LOC + frontend polling | async-vs-state races, the 29s dance |
| Harness | GA | the orchestration-infra layer | version/endpoint/model-swap plumbing |
| Memory | GA | ~3,500 LOC avoidable | dual-write coordination |
| Gateway | GA | ~450 LOC | tool-API drift, credential plumbing |
| Identity | GA | ~600 LOC | hand-rolled OAuth, signature bugs |
| Policy | GA | ~150 LOC | imperative gate drift, quota bugs |
| Observability | GA | ~80 LOC + upgrade | "where did the time go" |
| Code Interpreter | GA | sandbox infra | code-exec jailbreak surface |
| Browser Tool | GA | headless fleet | browser-automation ops + recording |
| Registry | Preview | taxonomy/tool mirror | tool/agent sprawl & duplication |
| Evaluations | Preview | ~200 LOC avoidable | "is this prompt a regression" |

---

## 7. Tooling & deployment — the CLI changed

There are now **two** toolchains. Know which one you're on; the verbs and the
config artifact differ.

| | **New — `@aws/agentcore`** (recommended) | **Legacy — `bedrock-agentcore-starter-toolkit`** |
|---|---|---|
| Package | `@aws/agentcore` (npm, Node 20+) | pip (Python); prints a deprecation banner |
| Verbs | `agentcore create` → `dev` → `deploy` → `invoke`; `add`, `status`, `logs`, `traces`, `destroy` | `agentcore configure` → `launch` → `invoke`, `status` |
| Config artifact | **`agentcore.json`** (+ auto-managed `cdk/`) | `.bedrock_agentcore.yaml` (hidden, gitignored) |
| Under the hood | AWS **CDK** synth/deploy | CodeBuild ARM64 container build |

`CLAUDE.md` and the §3 layout standardize on `agentcore.json` + `agentcore deploy`
— i.e. the **new CLI**. The new flow:

```bash
agentcore create --name MyAgent --framework Strands --model-provider Bedrock --build CodeZip
cd MyAgent
agentcore dev                 # local server, hot reload, agent inspector on :8080
agentcore deploy --plan       # preview the CDK diff
agentcore deploy              # build + deploy
agentcore invoke --prompt "..." --stream
agentcore add memory|gateway|credential|evaluator   # attach primitives
```

Frameworks scaffolded by `create`: Strands, LangGraph, CrewAI, AutoGen, Google ADK,
OpenAI Agents — plus IaC features for **CDK** and **Terraform**. Build types:
**CodeZip** (default) or **Container** (bring-your-own). The **Dockerfile is
generated**, not hand-written; it wraps the entrypoint with
`opentelemetry-instrument` when observability is on.

> If you inherit a repo using `.bedrock_agentcore.yaml` and `configure`/`launch`,
> it's on the legacy Python toolkit. New projects should use `@aws/agentcore`.
> When the bootstrap is unhealthy, keep a raw `cdk deploy` fallback documented —
> but fix the bootstrap rather than living on the workaround.

### Frontend transport (load-bearing details)

- **Payload is bytes; the response body is a stream you read.** boto3:
  `payload=json.dumps({...}).encode("utf-8")`, then `resp["response"].read()`.
  AWS SDK JS: read with `transformToWebStream().getReader()` — a `getReader()`
  loop, **not** `for await…of` (the latter is patchy pre-Chrome 124).
- **`runtimeSessionId` must be ≥ 33 chars.** Use a UUID. Reusing the same id pins
  you to the same warm microVM (session affinity) — that's the point.
- **Long read timeouts.** boto3 `read_timeout=900`, `retries={"max_attempts": 0}`;
  AWS SDK JS `FetchHttpHandler({ requestTimeout: 300_000 })`. The default
  (~30s) kills long turns.
- **Explicit `break` on the terminal event.** Stream EOF doesn't always propagate
  cleanly through CloudFront + Runtime proxies; break on `*_complete` / `error`.
- **RTK Query `queryFn` is the transport-swap bridge.** Expose agent mutations
  through `queryFn → invokeRuntimeOnce(client, payload)` — same hook signature,
  same `invalidatesTags`, no call-site edits when transport changes.

---

## 8. Migration playbook (existing REST/Lambda app)

Greenfield is strongly preferred (§4.3). If you must migrate an existing
Lambda-coordinator codebase, here's how the cutover actually goes.

- **Plan in *call surfaces*, not Lambdas or routes.** The unit of migration is the
  `(op, frontend caller)` pair. A Lambda that multiplexes ops by request-body shape
  costs `N × (port + transport + test)`, not `1×`. Name every op in the plan.
- **Phases are additive until ONE cutover phase.** Author the new path
  side-by-side; destructive deletes need the calling surface provably dead, which
  is only true after the frontend fully migrates. Most LOC and all risk land in
  that one final phase.
- **Stand up the streaming envelope first, on a `ping` op.** Heartbeats,
  `*_started` flushing, the `getReader()` loop, explicit break-on-terminal — prove
  them on the smallest op before any real op needs them.
- **Browser validation is the smoke test.** CLI smoke tests pass while the browser
  path is broken. The AgentCore Browser tool + Playwright gives a clean Chromium
  with known token state — the cheapest way to catch frontend/backend divergence.

### Gotchas that eat the most time (most surface as "the dialogue hangs at round N")

1. **`asyncio.run()` raises inside the Runtime event loop.** The entrypoint already
   runs a loop; `nest_asyncio` breaks the server. The SDK now drives handlers on a
   dedicated worker loop in a background thread — lean on that. If you spin your own
   stream, use a `concurrent.futures.ThreadPoolExecutor` with its own loop.
2. **Default SDK read timeout is ~30s** on the browser→Runtime call. Raise it
   (boto3 `read_timeout=900`; SDK JS `requestTimeout: 300_000`).
3. **Trailing post-JSON commentary** from the model on long contexts ("Extra data:
   line 1 column N"). Use `json.JSONDecoder().raw_decode(stripped)`, not `json.loads()`.
4. **`runtimeSessionId` < 33 chars** is rejected — use a UUID.
5. **Stream EOF doesn't propagate** cleanly through CloudFront + Runtime proxies —
   explicit `break` on the terminal event.

### AWS / AgentCore operational gotchas

- **Keep `agentcore deploy` healthy.** A CDKToolkit stack stuck in
  `REVIEW_IN_PROGRESS` fails the bootstrap pre-check; document a raw `cdk deploy`
  fallback, but fix the bootstrap rather than living on it.
- **Deploy context flags are load-bearing.** Omitting domain/cert context flags
  silently drops custom-domain CORS and flips frontend URLs to the CloudFront
  domain. Diff the synth before every deploy.
- **OTEL span sink (`aws/spans`) is AWS-reserved** and auto-creates on first span;
  you can't pre-create it. If the platform pre-wires its own TracerProvider and
  bypasses the signed exporter, spans 400 — `OTEL_TRACES_EXPORTER=none` silences
  the spam while spans still flow as CloudWatch log events.
- **Gateway authorizer is immutable post-create** — changing it recreates the
  Gateway and re-attaches all targets. Never ship `authorizerType: NONE` to
  anything external.
- **CodeZip silently drops a directory** whose name collides with a top-level
  package in the dependency tree (e.g. a dir literally named like a dependency).
  Rename it (`app_memory/`, not `memory/` if `memory` is a dep).
- **Evaluator quirks:** `description` max ~200 chars; `instructions` may treat
  `{…}` as placeholder syntax — keep output-schema text line-formatted, not JSON
  examples.

---

## 9. How this reads into the ContextEng PRD → tasks pipeline

This doc is the architecture spine of the ContextEng process. It feeds the two
generators directly:

1. **PRD ([`PRD_DevelopmentPrompt.md`](PRD_DevelopmentPrompt.md) → `PRD.md`).**
   A state-of-the-art PRD must, in its Architecture section, **(a)** declare the
   two compute paths (§3), **(b)** make the **Harness-vs-Runtime** decision
   explicitly (§4) with its rationale, and **(c)** include a *primitive-adoption
   ledger* — for each AgentCore primitive in §6, "adopt / defer / N-A" with the
   buy-vs-build reason. A PRD that says "Lambda behind API Gateway runs the agent"
   is, by this doc, wrong on arrival.
2. **Tasks ([`TaskListGenerator.md`](TaskListGenerator.md) → `tasks.md`).** The
   generator turns that PRD into AgentCore-shaped tasks: stand up the Runtime
   entrypoint + streaming envelope first; attach Memory / Gateway / Identity /
   Policy as discrete tasks; wire Observability and the Evaluator into the deploy;
   build the frontend SigV4 streaming client with the §7 transport details. The
   generator already bans the anti-pattern this doc exists to prevent — *"NEVER
   create tasks that require proxy servers; use direct AWS integrations."*

Write the adoption memo from the **ledger, not the feature list**: "Memory is GA"
is a feature; "we don't build dual-write coordination" is the operative value.
Count **bug categories**, not just lines — the 29s dance was a few hundred LOC, but
its absence retires an entire class of races that would otherwise live in your
tracker forever. Draw the **product/infrastructure line** first (§4.2 vs §6): that
line is the actual trade you're making.

---

*Originally consolidated from a production Lambda-coordinator → AgentCore Runtime
migration, then generalized and brought current with the GA platform (Runtime,
Memory, Gateway, Identity, Policy, Observability, Code Interpreter, Browser all GA;
Harness GA; Registry, Evaluations, Optimization in preview). Treat version-marked
facts as perishable and confirm against the live developer guide.*
