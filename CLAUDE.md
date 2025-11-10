# CLAUDE.md - YOUR_APP

## 🚫 CRITICAL CONSTRAINTS

### Absolute Prohibitions
1. **NO proxy servers or FastAPI** - Architecture is Frontend → API Gateway (REST) → Lambda only
2. **NO mock data** - Ever. Use real APIs. If debugging, delete immediately after
3. **NO WebSocket mixing** - REST-only interface (dedicated WebSocket infrastructure if needed)
4. **NO deployment outside us-west-2** - Region locked
5. **NO claiming success without verification** - Test and verify actual behavior, check actual data exists
6. **NO code deletion without dependency analysis** - Check helper functions, imports, cross-references first
7. **NO assuming API response structure** - Verify actual structure vs expectations
8. **NO documentation in root folder** - All .md files go to documents/
9. **NO creating tech debt** - Fix lint issues now. Fix errors now. No shortcuts
10. **NO committing code without explicit request** - Wait for user instruction
11. **NO adding comments unless requested** - Keep code clean
12. **NO skipping disclaimers** - Every feature needs "Educational only, not advice"

### Verification Protocol (MANDATORY)
Before stating "working", "functional", "success", or "complete":
1. Run actual tests
2. Check actual data exists in database/system
3. Verify end-to-end functionality

Making code changes ≠ working system. Never trust API success messages alone.

## ✅ MANDATORY ACTIONS

### Every Task
1. **Use tasks.md exclusively** - Track all work, update status immediately (never tasks.txt or variants)
2. **Search before creating** - Use Grep/Glob to find existing implementations first
3. **Read files directly** - No permission needed, check neighboring files for patterns
4. **Fix root causes** - Not symptoms
5. **Follow existing patterns** - Match codebase conventions
6. **Run lint/typecheck before completion**:
   - **Web**: `npm run lint` and `npm run typecheck`
   - **Backend (Python)**: Check package.json or pyproject.toml for linting commands (pylint, ruff, mypy)
   - **Infrastructure (CloudFormation)**: `cfn-lint` or `aws cloudformation validate-template`
   - **Infrastructure (Terraform)**: `terraform validate`, `terraform fmt -check`, `tflint`
   - **iOS/macOS**: SwiftLint (if configured)
   - **Android**: Android Lint and ktlint (if configured)
   - **Win11**: Platform-specific linting tools (if configured)

### Before Code Changes
- Analyze dependencies (helper functions, imports, type definitions)
- Verify API response structure (console.log or debugger)
- Test after any code removal (even small deletions can cascade)

### Code Standards
- **Backend**: Python 3.12+ with strict typing
- **Frontend**: TypeScript with strict typing
- **Security**: Client-side encryption for sensitive data, all API keys in .gitignore
- **Infrastructure**: CloudFormation/CDK only (backend/infrastructure/templates/)
- **Prefer editing existing files** over creating new ones

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
├── documents/            # All documentation and diagrams
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
- `documents/infrastructure.md` - Complete infrastructure details
- `documents/architecture_diagram.png` - System architecture

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
- See documents/UV Setup.md for initialization
- Dual account strategy:
  - S3 deployment (frontend): Account XXXXXXXXXX with --profile my_profile
  - Infrastructure (Lambda/DynamoDB/API Gateway): Account XXXXXXXXXX default profile

**Commands**: * Specify here

---

**Template Instructions** (for repository setup):
- Replace YOUR_APP, DATA_SOURCE_1, your-public-s3-bucket with actual values
- Search "* Specify here" and update with project-specific details
