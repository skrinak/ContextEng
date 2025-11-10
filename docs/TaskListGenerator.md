Convert the provided Product Requirements Document (PRD) into a comprehensive, executable task list saved to `tasks.md`.

## Output Format

File: `tasks.md`

Each task must include:
1. Checkbox: `- [ ]`
2. Hierarchical number: 1.1, 1.2.1, etc.
3. Description: Specific, actionable, atomic (completable in single session)
4. Status: `[pending]` `[in-progress]` `[completed]`
5. Verification: How to confirm completion
6. Dependencies: BLOCKED BY notation if applicable
7. Parallel markers: [PARALLEL: X.X, Y.Y] if concurrent execution possible
8. Tool hints: Which Claude Code tools/agents to use
9. CLAUDE.md references: Which project rules apply

Template:
```markdown
# Project: [Extract from PRD title]

## 1. Setup & Review
- [ ] 1.1 Review CLAUDE.md for project-specific constraints `[pending]`
  - Verification: List 3+ key constraints that apply to this PRD
  - Tool: Read CLAUDE.md directly

- [ ] 1.2 Review existing codebase structure `[pending]`
  - Verification: Document file structure and key patterns
  - Tool: Task agent with Explore subagent (thorough)

## 2. [Feature Name from PRD]
- [ ] 2.1 Search codebase for existing similar implementations `[pending]` [PARALLEL: 2.2]
  - Verification: Document findings or confirm no existing solution
  - Tool: Grep for keywords, then Read relevant files
  - Note: Per CLAUDE.md, prefer editing existing files over creating new

- [ ] 2.2 Review security requirements for [Feature] `[pending]` [PARALLEL: 2.1]
  - Verification: List all security/compliance requirements
  - Note: Extract from PRD section X.Y

- [ ] 2.3 Implement [specific component] `[pending]`
  - BLOCKED BY: 2.1, 2.2
  - Verification: Component renders/executes without errors
  - Note: Per CLAUDE.md, use TypeScript strict mode, no mock data
  - Tool: Edit existing files where possible, Write only if new file required

- [ ] 2.4 Test [component] functionality `[pending]`
  - BLOCKED BY: 2.3
  - Verification: All automated tests pass, manual testing completed
  - Tool: Bash to run test suite

- [ ] 2.5 Run lint and typecheck `[pending]`
  - BLOCKED BY: 2.4
  - Verification: Zero errors, zero warnings
  - Tool: Bash npm run lint && npm run typecheck

- [ ] 2.6 Verify no tech debt introduced `[pending]`
  - BLOCKED BY: 2.5
  - Verification: No TODO comments, no commented code, no mock data, no placeholder values
  - Tool: Grep for "TODO", "FIXME", "mock", "placeholder"

- [ ] 2.7 Git commit: [Feature] implementation complete `[pending]`
  - BLOCKED BY: 2.6
  - Verification: Clean git status, commit message follows repo conventions
  - Tool: Bash for git commands

## 3. [Next Feature]
[Repeat pattern from section 2]

## Final Tasks
- [ ] X.1 Run full integration tests `[pending]`
  - Verification: All test suites pass

- [ ] X.2 Human UX testing for [personas from PRD] `[pending]`
  - Verification: Each persona completes critical user journeys successfully

- [ ] X.3 Verify all PRD requirements implemented `[pending]`
  - Verification: Checklist of PRD sections with implementation references

- [ ] X.4 Update documentation `[pending]`
  - Verification: API docs, user guides, architecture diagrams current
```

## Task Atomicity Rules

- Each task completable in single Claude Code session
- If task requires >30min or >5 file edits, break into subtasks
- Granularity target: 15-20 tasks per major feature

## Required Task Sequence Per Feature

Pre-Implementation (ALWAYS):
1. Search existing codebase for similar implementation
2. Review CLAUDE.md for applicable constraints
3. Identify security/privacy requirements
4. Identify external dependencies (APIs, services, credentials)

Implementation (from PRD):
1. One task per discrete component/function
2. Environment setup if new services/tools required
3. Infrastructure if AWS/cloud resources needed
4. Data migration if schema changes required

Post-Implementation (ALWAYS):
1. Automated testing
2. Lint and typecheck
3. Tech debt verification (no TODOs, commented code, mocks)
4. Human UX testing at feature boundaries
5. Git commit at completion

Error Resilience (where applicable):
1. "If tests fail, debug and fix" after test tasks
2. "If API rate limited, implement backoff" for external APIs
3. "Verify actual data exists" after data creation tasks

## Parallel Task Criteria

Mark [PARALLEL: X.X, Y.Y] when:
- No shared file modifications
- No data dependencies between tasks
- Independent information gathering (searches, reads, reviews)

Example: Security review parallel to codebase search

## Tool Hints

Specify when:
- Large codebase exploration: "Tool: Task agent with Explore subagent"
- File pattern matching: "Tool: Glob for **/*.tsx pattern"
- Content search: "Tool: Grep with -A 5 context"
- MCP servers available: "Tool: Use mcp__database for query"
- Code execution: "Tool: Bash with proper conda/venv activation"

## CLAUDE.md Integration

Reference rules in task notes:
- "Per CLAUDE.md: No mock data - use real API"
- "Per CLAUDE.md: Edit existing files, avoid creating new"
- "Per CLAUDE.md: Include disclaimer for financial content"
- "Per CLAUDE.md: Verify via alpha URL http://..."

## Git Commit Rules

Add commit task after:
- Complete feature (all tests pass, no tech debt)
- Major milestone (multiple features form coherent unit)
- Infrastructure changes (CDK/CloudFormation updates)

NEVER commit:
- Mid-feature (partial implementation)
- With failing tests
- With tech debt (TODOs, commented code)

## Verification Examples

- Code tasks: "File X contains Y, tests pass, no errors"
- Search tasks: "Documented findings in task notes"
- Test tasks: "All tests pass, coverage >X%"
- Review tasks: "Listed N requirements/constraints"
- Deployment tasks: "Alpha URL loads without errors"

## Coverage Requirements

From PRD - ensure all included:
- Every feature has task sequence
- Every user persona has UX testing task
- Every security requirement has implementation + test
- Every compliance item has verification task
- Every external integration has API + error handling tasks
- Every data model has creation + migration task

From CLAUDE.md (if exists):
- Project constraints referenced in relevant tasks
- Deployment procedures in deployment tasks
- Testing procedures in test tasks
- Prohibited patterns called out

Standard requirements - always include:
- First task is CLAUDE.md review
- Security review for each major feature
- Automated testing after each feature
- Lint/typecheck before each commit
- Tech debt verification before each commit
- Human UX testing at strategic milestones
- Git commits at feature completion only
- Documentation updates in final tasks

## Anti-Patterns

NEVER create tasks that:
- Use mock data (except explicit testing purposes)
- Introduce tech debt (TODOs, commented code, placeholders)
- Skip security considerations
- Skip testing
- Batch all testing at end (test incrementally)
- Require proxy servers (use direct AWS integrations)
- Violate CLAUDE.md project rules
- Lack verification criteria
- Are too large (>5 file edits or >30min)
- Have unclear completion state

## Missing Context Handling

If PRD lacks detail:
- Security: Add generic security review tasks, flag for user clarification
- Testing: Add standard automated + manual UX testing
- Infrastructure: Add "Review infrastructure requirements" discovery task
- External APIs: Add "Identify and document API requirements" task

If CLAUDE.md doesn't exist:
- Omit CLAUDE.md references
- Apply general best practices (no mock data, test incrementally, etc.)

## Pre-Save Checklist

- [ ] File named exactly `tasks.md`
- [ ] Every task has checkbox, number, description, status, verification
- [ ] Hierarchical numbering sequential and consistent
- [ ] All PRD features covered
- [ ] First task is CLAUDE.md review (if CLAUDE.md exists)
- [ ] Security tasks included
- [ ] Testing tasks after each feature
- [ ] Tech debt checks before commits
- [ ] Git commits only at completion points
- [ ] Parallel tasks marked where applicable
- [ ] Dependencies marked with BLOCKED BY
- [ ] Tool hints for complex operations
- [ ] Verification criteria specific and testable
- [ ] No anti-patterns present

## Execute

1. Read the PRD completely
2. Generate tasks.md following all specifications above
3. Run through pre-save checklist
4. Save to `tasks.md`
5. Present summary: "Created X tasks across Y categories for [Project Name]"
