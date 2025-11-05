# CLAUDE.md - YOUR_APP

Development guidance for Claude Code when working with the YOUR_APP platform.

Replace uppercase names with your specifics, i.e. YOUR_APP, DATA_SOURCE_1, etc

## 🎯 PRIMARY DIRECTIVES (Check These First)

### 1. Architecture: AWS-Native REST API Only
- **Frontend → API Gateway (REST) → Lambda → AWS Services** (NO proxy servers, NO FastAPI, NO localhost:8000)
- **Region**: us-west-2 exclusively
- **API**: REST-only interface (NO WebSocket mixing - use dedicated WebSocket infrastructure if needed)
- **Services**: EventBridge (events), API Gateway (REST), Lambda (compute), DynamoDB (state)

### 2. Platform Requirements
- **React Web**: TypeScript, Redux Toolkit, RTK Query
- **Deployment**: `cd platforms/web && ./deploy-alpha.sh`
- **Alpha URL**: http://your-public-s3-bucket/alpha/

### 3. Compliance Mandatory
- **Every feature**: Include disclaimers ("Educational only, not advice")
- **Security**: SOC2 foundation, encryption everywhere (TLS 1.3, AES-256)

### Security
- **KMS Encryption**: All DynamoDB tables encrypted at rest
- **Secrets Manager**: API keys for external vendors
- **IAM**: Least-privilege Lambda execution roles


### CLAUDE.md Compliance
- **NO MOCK DATA**: Complete elimination verified via comprehensive code audit

## 🛠️ DEVELOPMENT STANDARDS

### Task Tracking & Progress Management
- **File**: All tasks tracked in `tasks.md` (NEVER create tasks.txt or other variants)
- **Status Updates**: Mark tasks as completed immediately upon finishing
- **In-Progress Marking**: Mark tasks as in-progress when actively working on them
- **Resilience**: Ensures continuity if Claude Code is interrupted, crashes, or rate limited
- **Recovery**: tasks.md is the single source of truth for project state and progress

### Before Writing Code
1. **SEARCH FIRST**: Use Grep/Glob to find existing implementations
2. **READ CONTEXT**: Check neighboring files for patterns and conventions
3. **NO MOCK DATA**: Use real APIs (DATA_SOURCE_1)
4. **USE EXISTING**: Prefer editing files over creating new ones

### When Writing Code
REQUIRED: TypeScript with strict typing
NO COMMENTS unless explicitly requested
Follow existing patterns in codebase
Client-side encryption for sensitive data

### API Integration
- **Data Sources** (Price Engine only):
  - DATA_SOURCE_1
  - DATA_SOURCE_2
  - DATA_SOURCE_3
- **Keys**: Store in AWS Secrets Manager 
  - **Source**: Initial keys from .env, then migrated to Secrets Manager
  - **Runtime**: Lambda functions use Secrets Manager exclusively
- **Rate Limiting**: Monitor from DATA_SOURCE with user experience warnings near limits

**Caching System**:
- No data caching

### Testing & Deployment
- **Tests**: Run existing test commands (check package.json)
- **Lint**: `npm run lint` and `npm run typecheck` before completion
- **Deploy**: Use automated script at `platforms/web/deploy-alpha.sh`
- **Verify**: Check alpha URL after deployment

## 📂 PROJECT STRUCTURE
```
YOUR_APP/
├── frontend/             # React web app for administration purposes only
├── backend/              # AWS Lambda functions
│   ├── infrastructure/   # CDK/CloudFormation
│   └── lambda/           # Business logic
└── docs/                 # Architecture, Diagrams, Developer and User Guide documentation
```

## 🗄️ BACKEND DATA STORES & APIS

### Complete Infrastructure Overview
**📋 Reference**: `docs/infrastructure.md`
**📊 Architecture Diagram**: `docs/architecture_diagram.png`

### DynamoDB Tables 
* Specify here

#### Core external data management 
### External Data Sources
* Specify here

**Other Data Sources**: 
* Specify here

### S3 Buckets (3 Total)
* Specify here

### API Gateway Endpoints (REST)
* Specify here

#### Admin APIs (x-admin-email required)
* Specify here. The following are examples only
```
GET  /dashboard                 # System dashboard status
GET  /health                    # System health
GET  /history/{symbol}          # Historical indicator time series
GET  /indicators/{symbol}       # Technical indicators
GET  /last-trade/{symbol}       # Last-Trade indicators with caching
POST /indicators/batch          # Bulk indicator processing for Signal Scanner
POST /tracking/{symbol}         # Add single tracked symbols
POST /tracking/batch/{symbols}  # Add multiple tracked symbols
PUT  /refresh/{symbol}          # Refresh prices
```


### AWS CLI Commands
```bash
# CRITICAL: AWS commands require conda initialization and activation
# Initialize conda first, then activate the aws environment

# Template for all AWS commands:
- See uv setup guide

# Dual AWS Account Strategy:
- S3 deployment (frontend): Account XXXXXXXXXX with --profile my_profile
- Infrastructure (Lambda, DynamoDB, API Gateway): Account XXXXXXXXXX with default profile

# S3 Deployment Commands (alpha hosting):
* Specify here

# Infrastructure Commands (price engine, admin, etc.):
* Specify here

# Example: Test Lambda function
* Specify here
```

## ❌ NEVER DO THIS

1.  **Create proxy servers** or use FastAPI
2.  **Add mock data** except for debugging (delete immediately)
3.  **Create documentation** unless explicitly requested
4.  **Commit code** unless explicitly asked
5.  **Add comments** unless requested
6.  **Skip disclaimers** 
7.  **Deploy outside us-west-2**
8. **Remove code without dependency analysis** - Always check for helper functions, imports, and cross-references before deletion
9. **Assume property names in API responses** - Always verify actual API structure vs frontend expectations
10. **Create documentation in root directory** - All new .md files must go to /docs/ directory
11. **No shortcuts** - When debugging discover root causes, never insert mock data or create tech debt.
12. **Never create tech debt** - when you see lint issues in the codebase, fix them now. When there's a UI or back end error, fix it now.
13. **NEVER claim functionality works until tested and verified** - Making code changes does NOT mean the system is working. Always test and verify actual behavior before claiming success.
14. **MANDATORY VERIFICATION PROTOCOL** - Before stating "working", "functional", "success", or "complete": (1) Run actual tests, (2) Check actual data exists, (3) Verify end-to-end functionality. NO EXCEPTIONS. 

## ✅ ALWAYS DO THIS

1. **Track progress in tasks.md** - Update task status (in-progress/completed) as you work
2. **Search before creating** new code
3. **Read files directly** without asking permission
4. **Fix root causes** not symptoms
5. **Test your changes** with existing test suites
6. **Include disclaimers** for sensitive content
7. **Follow existing patterns** in the codebase
8. **Run lint/typecheck** before marking complete
9. **Use CloudFormation/CDK** for all infrastructure changes (backend/infrastructure/templates/)
10. **Ensure infrastructure is rebuildable** - templates must be complete and error-free
11. **Analyze dependencies before removing code** - Check for helper functions, imports, type definitions
12. **Verify API response structure** - Use console.log or debugger to check actual vs expected property names
13. **Test after any code removal** - Even small deletions can cause cascading failures
14. **BEFORE CLAIMING SUCCESS: Verify actual data exists in database/system** - Never trust API success messages, always check the actual end result

