# CLAUDE.md - YOUR_APP

## 🚫 CRITICAL CONSTRAINTS

1. **NO proxy servers or FastAPI** - Architecture is Frontend → API Gateway (REST) → Lambda only
2. **NO hardcoded mock data** - Never inline fake data in source code. Test/mock data is fine if loaded from a data source (fixtures, seed files, test APIs).
3. **NO WebSocket in REST endpoints** - REST API stays REST-only. If real-time features are needed, build dedicated WebSocket infrastructure separately.
4. **NO deployment outside us-west-2** - Region locked
5. **NO documentation in root folder** - All .md files go to docs/
6. **NO committing code without explicit request** - Wait for user instruction
7. **NO adding comments unless requested** - Keep code clean
8. **NO skipping disclaimers** - Every feature needs "Educational only, not advice"
9. **NO calling python or pip directly** - Use `uv run` for execution and `uv pip` or `uv add` for package management. uv must be installed as a prerequisite.

## ✅ MANDATORY ACTIONS

### Every Task
1. **Use tasks.md exclusively** - Track all work, update status immediately (never tasks.txt or variants)
2. **Run lint/typecheck before completion**:
   - **Web**: `npm run lint` and `npm run typecheck`
   - **Backend (Python)**: Check package.json or pyproject.toml for linting commands (pylint, ruff, mypy)
   - **Infrastructure (CloudFormation)**: `cfn-lint` or `aws cloudformation validate-template`
   - **Infrastructure (Terraform)**: `terraform validate`, `terraform fmt -check`, `tflint`

### Before Code Changes
- **Read before writing** — Before modifying a function or module, read every file that imports or calls it. Do not skip this step to save time.
- **Match existing patterns** — If the codebase solves a similar problem already, use that approach. Do not introduce new patterns, libraries, or abstractions when an existing one works.
- Analyze dependencies (helper functions, imports, type definitions)
- Verify API response structure before relying on it
- Test after any code removal (even small deletions can cascade)

### Code Standards
- **Backend**: Python 3.12+ with strict typing
- **Frontend**: TypeScript with strict typing
- **Security**: Client-side encryption for sensitive data, all API keys in .gitignore
- **Infrastructure**: CloudFormation/CDK only (backend/infrastructure/templates/)

## 🏗️ ARCHITECTURE

**Stack**: Frontend → API Gateway (REST) → Lambda → AWS Services
**Region**: us-west-2 (exclusive)
**Services**: EventBridge (events), API Gateway (REST), Lambda (compute), DynamoDB (state)

**Frontend**:
- React Web: TypeScript, Redux Toolkit, RTK Query
- Deployment: `cd platforms/web && ./deploy-alpha.sh`
- Alpha URL: http://your-public-s3-bucket/alpha/

**Security & Compliance**:
- SOC2 foundation, TLS 1.3, AES-256 encryption
- KMS encryption for all DynamoDB tables
- Secrets Manager for API keys (runtime: Lambda uses Secrets Manager exclusively)
- IAM least-privilege execution roles
- Disclaimers required for every feature

**API Integration**:
- Data Sources: DATA_SOURCE_1, DATA_SOURCE_2, DATA_SOURCE_3
- Keys: .env → Secrets Manager migration
- Rate Limiting: Monitor DATA_SOURCE, warn users near limits
- No data caching

## 📂 PROJECT STRUCTURE

```
YOUR_APP/
├── .env                  # Local development only
├── .gitignore
├── backend/
│   ├── infrastructure/   # CDK/CloudFormation templates
│   └── lambda/           # Business logic
├── docs/                 # All documentation and diagrams
│   └── images/
├── frontend/
│   ├── android/
│   ├── ios/
│   ├── macos/
│   ├── web/              # React TypeScript app
│   └── win11/
├── tasks.md              # Single source of truth for progress
└── utils/                # Scripts and tools
```

## 🗄️ INFRASTRUCTURE REFERENCE

**Documentation**:
- `docs/infrastructure.md` - Complete infrastructure details
- `docs/architecture_diagram.png` - System architecture

**DynamoDB Tables**: * Specify here

**External Data Sources**: * Specify here

**S3 Buckets**: * Specify here

**API Gateway Endpoints (REST)**: * Specify here

**Admin APIs** (require x-admin-email header): * Specify here

Example endpoints:
```
GET  /dashboard                 # System status
GET  /health                    # Health check
GET  /history/{symbol}          # Historical data
GET  /indicators/{symbol}       # Technical indicators
POST /indicators/batch          # Bulk processing
POST /tracking/{symbol}         # Add tracked symbol
PUT  /refresh/{symbol}          # Refresh data
```

## 🔧 AWS OPERATIONS

**CRITICAL**: AWS commands require uv initialization first
- See docs/UV Setup.md for initialization
- Dual account strategy:
  - S3 deployment (frontend): Account XXXXXXXXXX with --profile my_profile
  - Infrastructure (Lambda/DynamoDB/API Gateway): Account XXXXXXXXXX default profile

**Commands**: * Specify here

---

**Template Instructions** (for repository setup):
- Replace YOUR_APP, DATA_SOURCE_1, your-public-s3-bucket with actual values
- Search "* Specify here" and update with project-specific details
