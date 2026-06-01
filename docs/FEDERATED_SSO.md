# Federated SSO: Google, GitHub, and enterprise (and where AgentCore Identity is *not* the answer)

Consolidated lessons from designing federated sign-in for a production agentic app
([xact.ai](https://xact.ai)): social login (Google, GitHub), enterprise SSO
(Okta/Azure AD/SAML/OIDC), forced MFA, and identity linking. Companion to
[`AGENTCORE_FIRST.md`](AGENTCORE_FIRST.md).

**The headline, because it's the most common mistake:** *human* sign-in
federation is **Cognito's** job, not AgentCore Identity's. Get this boundary
wrong and you build your login system in the wrong layer.

---

## 1. Two identity layers — do not conflate them

| | Human sign-in (who is the person) | Workload / outbound (what the agent may access) |
|---|---|---|
| **Owned by** | **Cognito User Pool** + federated IdPs | **AgentCore Identity** (credential vault + OAuth broker) |
| **Question** | "Is this Alice, and did she prove MFA?" | "Can the agent act on Alice's GitHub / call this tool on her behalf?" |
| **Examples** | Continue with Google · Continue with GitHub · Use SSO (Okta/Azure AD) | The app creating a repo on the user's GitHub · a Slack/Brave tool call · an inbound webhook reply token |
| **Output** | A Cognito JWT (your session) | A scoped, vended access token the agent uses against an external service |

AgentCore Identity is in [`AGENTCORE_FIRST.md` §Identity](AGENTCORE_FIRST.md#4-the-retirement-ledger--buy-vs-build-catalog). **This** doc is the other layer:
the one that puts the right human in front of the agent. They meet at exactly one
place — a `custom:*` claim on the Cognito token carrying your canonical user id —
and nowhere else.

### The "three GitHubs" test

A single product often has GitHub in *three* unrelated roles. If you can't name
which layer each belongs to, you'll consolidate them and regret it:

| Role | Layer | Credential |
|---|---|---|
| **Sign in with GitHub** (who is the user) | Human SSO → Cognito (via OIDC bridge, §3) | OAuth App, minimal scope (`read:user user:email`) |
| **Create a repo on the user's GitHub** (act on their behalf) | Workload → AgentCore Identity outbound OAuth | OAuth App, intrusive scope (`repo`) |
| **Read a public reference repo** | Neither | unauthenticated public reads (or a project PAT) |

**Do not consolidate the first two.** The login button must stay minimal-scope; an
agent that writes repos needs `repo`. One OAuth app can't be both without handing
every login a write token. Separate apps, separate layers.

---

## 2. Four decisions that set up everything

Make these on day one — retrofitting them under enterprise-deal pressure is the
failure mode.

1. **GitHub via an OIDC bridge, not a one-off backend hack.** GitHub's user OAuth
   does not issue OIDC `id_token`s, so Cognito can't federate it natively. A ~200-LOC
   bridge (§3) makes GitHub look identical to every other OIDC IdP — so you get *one*
   `post_confirmation`, *one* identity-claim shape, *one* linking codepath shared by
   Google, GitHub, Okta, and Azure AD. A backend-minted "GitHub session" that bypasses
   Cognito forces you to write every linking rule and identity invariant twice.
2. **The "Use SSO" button is email-domain discovery.** The canonical enterprise
   pattern (Slack/Notion/Figma/Linear): user types `alice@acme.com`, you look up the
   domain, redirect to that org's IdP. This forces you to build the load-bearing
   `Organizations` + `OrgDomains` data model *now*, so the first enterprise customer is
   one CDK IdP block + one `Organizations` row, not a schema project under deal pressure.
3. **MFA via a single computed claim, not per-IdP code.** A `pre_token` Lambda
   computes one `mfa_assured` boolean: true for password+TOTP, true if the IdP asserts
   `amr:["mfa"]`, true if the social provider reports 2FA on, false otherwise. The
   frontend redirects to `/enroll-mfa` when false. One gate covers Google-without-MFA
   today and enterprise-without-MFA later, with zero IdP-specific frontend code.
4. **Scope deliberately.** Apple Sign-In, for instance, is consumer-only and absent
   from enterprise IdP catalogs — it adds a Developer Program cost, a 6-month JWT-key
   rotator, and a private-relay-email edge case, none of which forward to SAML/OIDC.
   Include an IdP only if it earns its maintenance surface.

---

## 3. The GitHub OIDC bridge

The one genuinely novel piece. It exists so GitHub becomes "just another OIDC IdP"
and shares every line with Google/Okta/Azure. A tiny stateless service (Lambda +
HTTP API) implementing the OIDC provider contract:

| Method | Path | Purpose |
|---|---|---|
| GET | `/.well-known/openid-configuration` | OIDC discovery doc (static JSON, `Cache-Control: max-age=3600`) |
| GET | `/authorize` | validate `client_id`/`redirect_uri` allow-list, stash state (DDB, 60s TTL), redirect to GitHub |
| GET | `/oauth-callback` | GitHub redirects here post-consent; map back to Cognito state |
| POST | `/token` | exchange code → mint a **synthetic, KMS-signed RS256 `id_token`** + access token |
| GET | `/userinfo` | return `sub`/`email`/`email_verified`/`name`/`login`/`amr` for federation |
| GET | `/jwks` | public keys for `id_token` verification (Cognito caches 24h) |

Design notes that bite if you skip them:
- **Sign the `id_token` with KMS** (asymmetric RS256 key), publish the public half at
  `/jwks`. Never embed signing material in the Lambda.
- **`amr` is where MFA crosses over:** set `amr:["mfa"]` in the minted token iff GitHub
  reports `two_factor_authentication: true`, so decision #3's gate works for GitHub.
- **Lock `redirect_uri` to an exact allow-list** (just Cognito's `/oauth2/idpresponse`).
  The bridge is an open redirector if you don't.
- The bridge is invisible to the SPA — the SPA only ever talks to the Cognito Hosted UI.

---

## 4. Identity linking — and strict separation

The rule that keeps personal and enterprise identities from contaminating each other:

- **Personal accounts auto-link by verified email.** First Google/GitHub sign-in of an
  email that already has a password account → `AdminLinkProviderForUser` in
  `post_confirmation`, so the user lands on their existing data. Same `accountKind` +
  same verified email is the link condition.
- **Enterprise accounts NEVER link.** An `enterprise` identity is keyed to its org/tenant
  and stays separate from any personal account with the same email. Strict separation —
  the linking codepath refuses to run for `enterprise`.

### Two non-obvious invariants (both cost a debugging cycle if missed)

1. **Cognito's `identities` claim is a JSON *string*, not an array.** Every consumer must
   `json.loads` it. Put a `_split_identity` helper in `shared/auth_utils.py` and use it
   everywhere; never index the raw claim.
2. **`sub` ≠ your canonical `userId` momentarily after the first federated sign-in of an
   existing email.** Cognito issues a *fresh* `sub` for the new federated identity
   *before* `AdminLinkProviderForUser` runs. To keep backend handlers correct in that gap,
   have `pre_token` write `custom:xactUserId` (looked up via an `email-index` GSI), and
   make `get_user_id()` read `custom:xactUserId` with `sub` as fallback. Without this,
   the user transiently looks like a brand-new account.

---

## 5. Enterprise SSO

- **Data model first** (decision #2): `Organizations` (the tenant) + `OrgDomains` (verified
  email domains → providerName). `/auth/discover?email=` returns the provider; the SPA then
  hits the *same* Cognito authorize/callback path as Google.
- **Native vs bridged.** Cognito federates SAML and OIDC IdPs natively
  (`UserPoolIdentityProviderSaml` / `...Oidc`). For the long tail of corporate IdPs, a
  managed bridge (e.g. WorkOS) collapses Okta/Azure AD/Ping/OneLogin into one OIDC
  connection so you don't maintain N SAML metadata blobs.
- **Onboarding is an operator runbook, not a deploy.** Adding a customer = create the IdP
  (one CDK block or one WorkOS connection) + one `Organizations` row + map their domains.
  Write the customer-facing setup instructions and the rollback once; reuse per customer.
- **Carry `custom:tenantId` / `custom:accountKind` from t=0**, even before the first
  enterprise customer. They're free to add to the User Pool schema now and impossible to
  backfill cleanly later (Cognito custom attributes are immutable once created).

---

## 6. Console / infra gotchas

- **Cognito custom domain cert lives in us-east-1** regardless of the User Pool's region.
  Any bridge HTTP API cert lives in the pool's region. Two certs, two regions.
- **Custom Cognito attributes (`custom:*`) are immutable after creation** — you can't
  change type or delete them. Decide `accountKind`/`tenantId`/`xactUserId` up front.
- **Apple's `client_secret` is a JWT that expires every 6 months** — if you do include
  Apple, you owe a scheduled rotator. (One more reason to scope it out unless you need it.)
- **The same secret name surviving a rename ≠ the secret being used.** Audit what code
  actually reads each IdP secret; dead OAuth secrets accumulate. (See the
  `contextbuilder/github-token` post-mortem in the xact.ai PRD — a "live secret" that no
  code had read in months.)

---

## 7. Two failure modes to avoid

1. **Shipping a GitHub button as a one-off backend hack.** It won't fit Cognito's
   federation pipe; when enterprise SSO arrives you rewrite every linking rule twice. Build
   the OIDC bridge so GitHub is just another IdP from the start.
2. **Hiding SSO until a customer signs.** Building `Organizations`/`OrgDomains`/the IdP
   factory under deal pressure means making weeks-worth of schema decisions in days. Build
   the model now (it's cheap); flip the button on when you're ready.

---

*Source: the xact.ai federated-login design (Google + GitHub + enterprise SSO, MFA, linking).
Generalized here so future ContextEng projects inherit the architecture — especially the
Cognito-vs-AgentCore-Identity boundary — instead of relearning it the hard way.*
