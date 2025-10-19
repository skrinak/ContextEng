# ContextEng

Templates and configurations for context engineering with AI code assistants.

## Purpose

This repository provides templates for managing context in AI code writing tools such as Claude Code and Kiro. These templates establish project guidelines, structure conventions, and development practices for AI assistants.

Context window management is critical in AI-assisted development. Regular use of the `/clear` command helps maintain optimal performance. A working pattern: use `/clear`, then read core project files (README.md, CLAUDE.md, TASKS.md, .env). Maintaining these files enables consistent architecture, clear development guidelines, and focused debugging.

## What's Included

- **CLAUDE.md** - Comprehensive project instructions template for Claude Code
- **claude-template.md** - Starter template for creating project-specific instructions
- **settings.json** - Example configuration settings
- **env.example** - Environment variable template
- **2025-10-14 - UV Setup.md** - UV package manager setup guide

## Getting Started

1. Copy the relevant template files to your project
2. Customize `CLAUDE.md` with your project-specific details
3. Replace placeholder text (YOUR_APP, DATA_SOURCE_1, etc.) with your actual values
4. Configure settings according to your development workflow

## Benefits

- Consistent AI behavior across team members
- Reduced repetitive instructions
- Enforced development standards
- Defined architectural patterns
- Structured debugging workflows

## Memory Management

### Core Principles

Context window size directly impacts AI assistant performance. Effective context management can improve performance by 39% ([Anthropic research](https://www.anthropic.com/news/context-management)).

### Essential Commands

**`/clear`** - Reset context window between tasks. Use regularly to maintain performance.

**`/context`** - Inspect token usage and optimize MCP tools.

**`/compact`** - Compress current session to reduce token count (processing time: 1+ minutes).

**`/resume`** - Switch between previous sessions.

### File Organization

**Project Memory** (CLAUDE.md):
- Project-specific guidelines loaded at session start
- Keep minimal to reduce token consumption
- Follow cascaded system approach ([Claude Code best practices](https://www.anthropic.com/engineering/claude-code-best-practices))

**Ad-Hoc Documentation** (docs/):
- Store occasional-use information separately
- Reference via `@docs/filename.md` to avoid loading unnecessary content
- Load context on-demand for complex analysis

### Context Engineering Patterns

**Core Strategies**:
1. **Writing** - Create persistent information stores
2. **Selecting** - Load relevant information when needed
3. **Compressing** - Minimize token usage
4. **Isolating** - Structure information by concern

**Implementation**:
- Break tasks into discrete units; use `/clear` between completions
- Delegate verification and investigation to subagents
- Maintain examples folder for pattern reference
- Document session context before closing
- Import only relevant code sections
- Preserve project hierarchy in references

### Advanced Features

**Context Editing** - Automatically removes stale tool calls when approaching token limits. Reduces token consumption by 84% in extended sessions. [Details](https://www.anthropic.com/news/context-management)

**Memory Tool** - File-based storage for information outside the context window. Maintains knowledge bases and project state across sessions.

**Context Awareness** - Claude Sonnet 4.5 and Haiku 4.5 track remaining context window throughout conversations.

## AWS Integration

### Tools

**[Amazon Q Developer](https://aws.amazon.com/q/developer/)** - AI coding assistant for AWS. Code acceptance rates: 37-60%. Language support: Python, Java, JavaScript, TypeScript, C#, Go, Rust, PHP, Ruby, Kotlin, C, C++, shell scripting, SQL, Scala, JSON, YAML, HCL.

**[AWS MCP Servers](https://aws.amazon.com/blogs/machine-learning/introducing-aws-mcp-servers-for-code-assistants-part-1/)** - Model Context Protocol servers for AWS development workflows.

### Implementation Patterns

- **IaC Translation**: Automated translation between infrastructure frameworks. [Guide](https://aws.amazon.com/blogs/compute/infrastructure-as-code-translation-for-serverless-using-ai-code-assistants/)
- **Security Scanning**: Vulnerability detection, credential exposure, log injection analysis
- **CI/CD**: Test generation, contract validation, pre-production failure detection
- **Compliance**: [FedRAMP and DoD CC SRG](https://aws.amazon.com/blogs/publicsector/building-an-ai-coding-assistant-on-aws-a-guide-for-federal-agencies/) implementation guidance

## Resources

### Documentation

- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code)
- [Context Windows Guide](https://docs.claude.com/en/docs/build-with-claude/context-windows)
- [Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [AWS Amazon Q Developer](https://aws.amazon.com/q/developer/)

### Thought Leaders

**[IndyDevDan](https://www.youtube.com/@indydevdan)** - Agentic engineering and principled AI coding
- [Principled AI Coding (PAIC)](https://agenticengineer.com/principled-ai-coding) - Comprehensive course on AI coding fundamentals
- [Tactical Agentic Coding (TAC)](https://agenticengineer.com/tactical-agentic-coding) - Advanced course on agent orchestration and production deployment
- Focuses on building living software with Claude Code, spec-based coding, and agentic workflows
- [YouTube](https://www.youtube.com/@indydevdan) | [Website](https://indydevdan.com/) | [X/Twitter](https://x.com/indydevdan)

**[Cole Medin](https://github.com/coleam00)** - Context engineering resources and implementation patterns
- [Context Engineering Introduction](https://github.com/coleam00/context-engineering-intro)
- Dynamous AI community - Context Engineering Hub
- Product Requirements Prompts (PRPs) methodology
- [LinkedIn](https://www.linkedin.com/in/cole-medin-727752184/) | [GitHub](https://github.com/coleam00)

### Additional Reading

- [Practical Context Engineering](https://abvijaykumar.medium.com/practical-context-engineering-for-vibe-coding-with-claude-code-6aac4ee77f81)
- [Memory Management Tips](https://www.geeky-gadgets.com/claude-code-memory-management-tips/)
- [Context Engineering Guide](https://www.datacamp.com/blog/context-engineering) (DataCamp)
- [AI Coding Context Management](https://prompt.16x.engineer/blog/ai-coding-context-management)
- [Google Cloud AI Assistant Best Practices](https://cloud.google.com/blog/topics/developers-practitioners/five-best-practices-for-using-ai-coding-assistants)

## Contributing

Submit issues or pull requests to improve these templates.
