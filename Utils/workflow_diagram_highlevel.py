#!/usr/bin/env python3
"""
High-Level Workflow Diagram Generator for ContextEng AI Development Process
Narrative-style process flow from PRD to completion
"""

import graphviz

dot = graphviz.Digraph('AI_Development_Workflow_HighLevel', comment='High-Level Workflow')

dot.attr(rankdir='LR', splines='ortho', nodesep='0.7', ranksep='1.3')
dot.attr('graph', fontname='Arial', fontsize='13', bgcolor='white', pad='1.0')
dot.attr('node', fontname='Arial', fontsize='11', style='filled', margin='0.5')
dot.attr('edge', fontname='Arial', fontsize='10', penwidth='2.5')

# Start
dot.node('start', '🎯 Start:\nProject Concept',
         shape='ellipse', fillcolor='#A23B72', fontcolor='white',
         width='2.2', height='1.0', fontsize='12')

# Phase 1: PRD Development
dot.node('prd', '''📋 PRD Development

The process begins with writing
a well-articulated PRD using the
PRD Development Prompt provided
in this repo

Iterate over the prompt for several
days, speaking with stakeholders
and integrating knowledge of
agentic AI software development

Output: PRD.md (finalized)''',
         shape='box', fillcolor='#2E86AB', fontcolor='white',
         width='3.0', height='2.4', fontsize='10')

# Phase 2: Task Generation
dot.node('tasks', '''📝 Task Generation

Once the PRD.md is finalized, the
development team and stakeholders
use the Task List Generator.md to
create a comprehensive task list

The task list is hierarchical with
dependencies and parallel execution
opportunities identified

Output: tasks.md''',
         shape='box', fillcolor='#7209B7', fontcolor='white',
         width='3.0', height='2.4', fontsize='10')

# Phase 3: Iterative Development
dot.node('development', '''💻 Iterative Development

Now you're ready to develop code

Continually clear context in your AI
development agent, then read the
foundational documents (CLAUDE.md,
README.md, .env) before iterating on
each phase of the task list

Clear and refresh after each phase,
though sometimes clearing should
occur within a phase as needed

Output: Working code''',
         shape='box', fillcolor='#06A77D', fontcolor='white',
         width='3.0', height='2.4', fontsize='10')

# Phase 4: Completion
dot.node('completion', '''✅ Completion

Verify all tasks are completed,
run comprehensive tests, and
deploy the working solution to
production

Final validation ensures the
implementation matches the
original PRD requirements

Output: Production release''',
         shape='box', fillcolor='#52B788', fontcolor='white',
         width='3.0', height='2.4', fontsize='10')

# Success
dot.node('success', '🎊 Success:\nProject Complete',
         shape='ellipse', fillcolor='#6A994E', fontcolor='white',
         width='2.2', height='1.0', fontsize='12')

# Main flow arrows with descriptive labels
dot.edge('start', 'prd', label='Begin with\nrequirements', fontsize='9', color='#333333')
dot.edge('prd', 'tasks', label='PRD finalized,\ngenerate tasks', fontsize='9', color='#333333')
dot.edge('tasks', 'development', label='Tasks defined,\nstart coding', fontsize='9', color='#333333')
dot.edge('development', 'completion', label='Code complete,\nverify & deploy', fontsize='9', color='#333333')
dot.edge('completion', 'success', label='Deployed', fontsize='9', color='#333333')

# Memory Management note
dot.node('memory_note',
         '''🧠 Memory Management Protocol

Context management is critical throughout development.
Use /clear to reset context, /context to view current state,
/compact to compress history, and /resume to continue work.

Refresh after each phase or when context exceeds 80% capacity.
Strategic memory management provides 39% performance improvement.''',
         shape='note', fillcolor='#FFF9E3', fontcolor='#333333',
         fontsize='10', style='filled', width='3.5')

dot.render('workflow_diagram_highlevel', format='png', cleanup=True)

print("✅ High-level workflow diagram generated: workflow_diagram_highlevel.png")
print("\nNarrative Flow:")
print("  The process begins with writing a well-articulated PRD using the")
print("  PRD Development Prompt. Iterate for several days with stakeholders.")
print("  Once finalized, use Task List Generator.md to create tasks.md.")
print("  Then develop code while continually clearing context and reading")
print("  foundational documents. Clear after each phase, or within phases")
print("  as needed. Finally, verify, test, and deploy to production.")
print("\nKey Features:")
print("  • Narrative descriptions (not bullets)")
print("  • Icons for visual clarity (🎯📋📝💻✅🎊🧠)")
print("  • Left-to-right progression")
print("  • Clear phase transitions")
