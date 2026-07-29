#!/usr/bin/env python3
"""
Workflow Diagram Generator for ContextEng AI Development Process
Creates a comprehensive visual representation of the PRD → Tasks → Development workflow
Using graphviz with proper process flow diagram shapes

Layout: Vertical phase stacking (top to bottom) with horizontal flow within each phase
Reading flow: Left-to-right within phases, top-down between phases
"""

import graphviz

dot = graphviz.Digraph('AI_Development_Workflow', comment='AI-Assisted Development Workflow')

dot.attr(rankdir='TB', splines='ortho', nodesep='0.6', ranksep='1.0', newrank='true')
dot.attr('graph', fontname='Arial', fontsize='12', bgcolor='white', pad='0.8', compound='true')
dot.attr('node', fontname='Arial', fontsize='10', style='filled', margin='0.3')
dot.attr('edge', fontname='Arial', fontsize='9')

with dot.subgraph(name='cluster_phase1') as phase1:
    phase1.attr(label='Phase 1: PRD Development\n(PRD_DevelopmentPrompt.md)',
                style='rounded', color='#2E86AB', fontsize='12', fontcolor='#2E86AB',
                labelloc='t', labeljust='l')

    phase1.attr(rank='same')

    phase1.node('start', 'Start:\nProject Concept',
                shape='ellipse', fillcolor='#A23B72', fontcolor='white', width='1.3', height='0.8')
    phase1.node('round1', 'Round 1:\nFoundation\n(Personas, AWS)',
                shape='box', fillcolor='#C73E1D', fontcolor='white', width='1.5')
    phase1.node('round2', 'Round 2:\nTechnical Deep Dive\n(Infrastructure, APIs)',
                shape='box', fillcolor='#C73E1D', fontcolor='white', width='1.8')
    phase1.node('round3', 'Round 3:\nImplementation\n(Deployment, Testing)',
                shape='box', fillcolor='#C73E1D', fontcolor='white', width='1.7')
    phase1.node('round4', 'Round 4:\nClaude Optimization\n(Task Decomposition)',
                shape='box', fillcolor='#C73E1D', fontcolor='white', width='1.7')
    phase1.node('prd_output', 'PRD.md\n(Complete)',
                shape='note', fillcolor='#6A994E', fontcolor='white', width='1.2')

    phase1.node('stakeholder', 'Stakeholder\nConsultation',
                shape='trapezium', fillcolor='#F18F01', fontcolor='white', width='1.5')

dot.edge('start', 'round1', label='Begin', fontsize='8')
dot.edge('round1', 'round2', label='Iterate', fontsize='8')
dot.edge('round2', 'round3', label='Refine', fontsize='8')
dot.edge('round3', 'round4', label='Optimize', fontsize='8')
dot.edge('round4', 'prd_output', label='Output', fontsize='8')

dot.edge('stakeholder', 'round1', label='Feedback', style='dashed', color='#F18F01', fontsize='8')
dot.edge('round4', 'stakeholder', label='Days of\nRefinement',
         style='dashed', color='#F18F01', fontsize='8', dir='both')

with dot.subgraph(name='cluster_phase2') as phase2:
    phase2.attr(label='Phase 2: Task Generation\n(Task List Generator.md)',
                style='rounded', color='#7209B7', fontsize='12', fontcolor='#7209B7',
                labelloc='t', labeljust='l')

    phase2.attr(rank='same')

    phase2.node('task_input', 'Input:\nPRD.md',
                shape='parallelogram', fillcolor='#6A994E', fontcolor='white', width='1.2')
    phase2.node('analyze', 'Analyze\nRequirements',
                shape='box', fillcolor='#560BAD', fontcolor='white', width='1.4')
    phase2.node('decompose', 'Decompose into\nHierarchical Tasks',
                shape='box', fillcolor='#560BAD', fontcolor='white', width='1.7')
    phase2.node('dependencies', 'Map Dependencies\n& Parallel Work',
                shape='box', fillcolor='#560BAD', fontcolor='white', width='1.7')
    phase2.node('verification', 'Add Verification\nCriteria',
                shape='box', fillcolor='#560BAD', fontcolor='white', width='1.5')
    phase2.node('tasks_output', 'tasks.md\n[pending]\nHierarchical',
                shape='note', fillcolor='#6A994E', fontcolor='white', width='1.3')

dot.edge('prd_output', 'task_input', label='Feed PRD', fontsize='8')
dot.edge('task_input', 'analyze', fontsize='8')
dot.edge('analyze', 'decompose', fontsize='8')
dot.edge('decompose', 'dependencies', fontsize='8')
dot.edge('dependencies', 'verification', fontsize='8')
dot.edge('verification', 'tasks_output', label='Generate', fontsize='8')

with dot.subgraph(name='cluster_phase3') as phase3:
    phase3.attr(label='Phase 3: Iterative Development\n(Claude Code Agent)',
                style='rounded', color='#06A77D', fontsize='12', fontcolor='#06A77D',
                labelloc='t', labeljust='l')

    phase3.node('clear_context', '/clear\nReset Context',
                shape='box', fillcolor='#048A81', fontcolor='white', width='1.3')
    phase3.node('load_foundation', 'Load Foundation:\nCLAUDE.md\nREADME.md\n.env',
                shape='parallelogram', fillcolor='#048A81', fontcolor='white', width='1.7')
    phase3.node('read_tasks', 'Read:\ntasks.md',
                shape='parallelogram', fillcolor='#048A81', fontcolor='white', width='1.2')
    phase3.node('select_task', 'Select Task(s)\nfrom tasks.md',
                shape='box', fillcolor='#06A77D', fontcolor='white', width='1.5')
    phase3.node('mark_progress', 'Mark\n[in-progress]',
                shape='box', fillcolor='#06A77D', fontcolor='white', width='1.3')
    phase3.node('execute_parallel', 'Execute Tasks\n(Parallel when\nindependent)',
                shape='ellipse', fillcolor='#05668D', fontcolor='white', width='1.7', height='1.0')
    phase3.node('execute_serial', 'Execute Task\n(Serial when\ndependent)',
                shape='box', fillcolor='#05668D', fontcolor='white', width='1.5')
    phase3.node('mark_complete', 'Mark\n[completed]',
                shape='box', fillcolor='#06A77D', fontcolor='white', width='1.3')
    phase3.node('phase_complete', 'Phase\nComplete?',
                shape='diamond', fillcolor='#F18F01', fontcolor='white', width='1.5', height='1.1')
    phase3.node('refresh_needed', 'Context\nRefresh\nNeeded?',
                shape='diamond', fillcolor='#F18F01', fontcolor='white', width='1.5', height='1.1')

dot.edge('tasks_output', 'clear_context', label='Start Dev', fontsize='8')

dot.edge('clear_context', 'load_foundation', fontsize='8')
dot.edge('load_foundation', 'read_tasks', fontsize='8')
dot.edge('read_tasks', 'select_task', fontsize='8')
dot.edge('select_task', 'mark_progress', fontsize='8')
dot.edge('mark_progress', 'execute_parallel', label='Independent', fontsize='8')
dot.edge('execute_parallel', 'execute_serial', label='Dependent', fontsize='8')
dot.edge('execute_serial', 'mark_complete', fontsize='8')
dot.edge('mark_complete', 'phase_complete', fontsize='8')

dot.edge('phase_complete', 'refresh_needed', label='More Tasks', fontsize='8')
dot.edge('refresh_needed', 'clear_context', label='Yes\n(Complex/Errors)',
         color='#F18F01', fontsize='8', style='dashed', constraint='false')
dot.edge('refresh_needed', 'select_task', label='No (Simple)',
         color='#2E86AB', fontsize='8', constraint='false')

with dot.subgraph(name='cluster_completion') as completion:
    completion.attr(label='Completion',
                    style='rounded', color='#6A994E', fontsize='12', fontcolor='#6A994E',
                    labelloc='t', labeljust='l')

    completion.attr(rank='same')

    completion.node('verify_all', 'Verify:\nAll Tasks\n[completed]',
                    shape='box', fillcolor='#52B788', fontcolor='white', width='1.4')
    completion.node('deploy', 'Deploy:\n./deploy-alpha.sh',
                    shape='box', fillcolor='#52B788', fontcolor='white', width='1.5')
    completion.node('success', 'Success:\nProject Complete',
                    shape='ellipse', fillcolor='#6A994E', fontcolor='white', width='1.6', height='0.8')

dot.edge('phase_complete', 'verify_all', label='All Phases\nComplete',
         fontsize='8', color='#6A994E', penwidth='2')
dot.edge('verify_all', 'deploy', fontsize='8')
dot.edge('deploy', 'success', fontsize='8')

with dot.subgraph(name='cluster_memory') as memory:
    memory.attr(label='Memory Management Protocol',
                style='rounded,dashed', color='#A23B72', fontsize='11', fontcolor='#A23B72',
                labelloc='t')

    memory.node('memory_protocol',
                '''Context Commands:
/clear - Reset context
/context - View current
/compact - Compress
/resume - Continue

When to Refresh:
• After each phase
• Within phase (complex)
• On errors/rate limits
• Context > 80%

39% Performance Boost''',
                shape='note', fillcolor='#FFF9E3', fontcolor='#333333',
                width='2.3', style='filled', fontsize='9')

dot.render('workflow_diagram', format='png', cleanup=True)

print("✅ Workflow diagram generated: workflow_diagram.png")
print("\nDiagram Layout:")
print("• TOP-DOWN phase stacking (vertical)")
print("• LEFT-TO-RIGHT flow within each phase (horizontal)")
print("• Reading pattern: Left-to-right, top-down")
print("\nPhase Structure:")
print("  Phase 1 (top)    → PRD Development with stakeholder loop")
print("       ↓")
print("  Phase 2          → Task Generation")
print("       ↓")
print("  Phase 3          → Iterative Development with decision loops")
print("       ↓")
print("  Completion       → Verify, Deploy, Success")
print("\n  Memory Protocol  → Side reference panel")
