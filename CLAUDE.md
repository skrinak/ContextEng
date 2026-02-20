# CLAUDE.md

## Constraints

Never do these things:

- Never add a proxy server or FastAPI layer. The architecture is Frontend → API Gateway (REST) → Lambda. No exceptions.
- Never hardcode mock data in source code. Test/mock data is acceptable only when loaded from a data source (fixtures, seed files, test APIs).
- Never add WebSocket to REST endpoints. REST API stays REST-only. Build dedicated WebSocket infrastructure separately if real-time features are needed.
- Never deploy outside us-west-2.
- Never place .md files in the root folder. All documentation goes in docs/.
- Never commit code unless the user explicitly asks.
- Never add code comments unless the user explicitly asks.
- Never omit the disclaimer "Educational only, not advice" from any feature.
- Never call python or pip directly. Use `uv run` for execution, `uv pip` or `uv add` for package management. uv is a prerequisite.

## Before every task

1. Track work in tasks.md. Update status immediately. Never use tasks.txt or other variants.
2. Run lint/typecheck before marking work complete:
   - Web: `npm run lint` and `npm run typecheck`
   - Python: check pyproject.toml for lint commands (pylint, ruff, mypy)
   - CloudFormation: `cfn-lint` or `aws cloudformation validate-template`
   - Terraform: `terraform validate`, `terraform fmt -check`, `tflint`

## Before modifying code

1. Read before writing. Before modifying a function or module, read every file that imports or calls it. Do not skip this step.
2. Match existing patterns. If the codebase already solves a similar problem, use that approach. Do not introduce new patterns, libraries, or abstractions when an existing one works.
3. Analyze dependencies: helper functions, imports, type definitions.
4. Verify API response structure before relying on it.
5. Test after any code removal. Even small deletions can cascade.

## Code standards

- Backend: Python 3.12+ with strict typing
- Frontend: TypeScript with strict typing
- Security: client-side encryption for sensitive data, all API keys in .gitignore
- Infrastructure: CloudFormation/CDK only, templates in backend/infrastructure/

## Architecture

Stack: Frontend → API Gateway (REST) → Lambda → AWS Services
Region: us-west-2 only
Services: EventBridge (events), API Gateway (REST), Lambda (compute), DynamoDB (state)

Frontend: React Web with TypeScript, Redux Toolkit, RTK Query
Deploy frontend: `cd platforms/web && ./deploy-alpha.sh`
Alpha URL: http://your-public-s3-bucket/alpha/

Security: SOC2 foundation, TLS 1.3, AES-256, KMS on all DynamoDB tables, Secrets Manager for API keys at runtime, IAM least-privilege roles.

Data sources: DATA_SOURCE_1, DATA_SOURCE_2, DATA_SOURCE_3
API keys: .env locally, Secrets Manager in production
Rate limiting: monitor DATA_SOURCE usage, warn users near limits
No data caching.

## Project structure

```
YOUR_APP/
├── .env                  # Local dev only
├── backend/
│   ├── infrastructure/   # CDK/CloudFormation templates
│   └── lambda/           # Business logic
├── docs/                 # All documentation
├── frontend/
│   ├── android/
│   ├── ios/
│   ├── macos/
│   ├── web/              # React TypeScript app
│   └── win11/
├── tasks.md              # Task tracking
└── utils/                # Scripts and tools
```

## Infrastructure reference

Docs: `docs/infrastructure.md`, `docs/architecture_diagram.png`

DynamoDB tables: [specify]
External data sources: [specify]
S3 buckets: [specify]
API Gateway endpoints (REST): [specify]
Admin APIs (require x-admin-email header): [specify]

Example endpoints:
```
GET  /dashboard
GET  /health
GET  /history/{symbol}
GET  /indicators/{symbol}
POST /indicators/batch
POST /tracking/{symbol}
PUT  /refresh/{symbol}
```

## AWS operations

Run uv initialization before any AWS commands. See docs/UV Setup.md.

Two AWS accounts:
- Frontend S3 deployment: account XXXXXXXXXX, use `--profile my_profile`
- Infrastructure (Lambda/DynamoDB/API Gateway): account XXXXXXXXXX, default profile

Commands: [specify]
