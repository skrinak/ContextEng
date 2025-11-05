# Utils - Workflow Diagram Generator

This directory contains utilities for generating visual documentation of the AI-assisted development workflow used in ContextEng projects.

## 📋 Contents

### High-Level Diagrams (Simple Process Flow) ⭐ NEW

**Consolidated view - left-to-right process flow:**
- `workflow_diagram_highlevel.drawio` - **Draw.io** format
- `workflow_diagram_highlevel.mmd` - **Mermaid** format
- `workflow_diagram_highlevel.puml` - **PlantUML** format
- `workflow_diagram_highlevel.png` - Generated PNG
- `workflow_diagram_highlevel.py` - Python generator script

**Simple flow:** Start → PRD Development → Task Generation → Iterative Development → Completion → Success

### Detailed Diagrams (Full Internal Processes)

**Complete view with all internal steps:**
- `workflow_diagram.drawio` - **Draw.io** XML format (recommended for manual editing)
- `workflow_diagram.mmd` - **Mermaid** diagram format (markdown-compatible)
- `workflow_diagram.puml` - **PlantUML** format (text-based UML)
- `workflow_diagram.png` - Generated PNG from Python/Graphviz script

**Generator Files:**
- `generate_workflow_diagram.py` - Python/Graphviz script for detailed PNG
- `workflow_diagram_highlevel.py` - Python/Graphviz script for high-level PNG
- `requirements.txt` - Python dependencies (graphviz)

## 🎨 Available Formats

### 1. Draw.io (Recommended for Manual Editing)
**File:** `workflow_diagram.drawio`

The most flexible format for manual editing and precise layout control.

**How to use:**
1. Open [draw.io](https://app.diagrams.net/) or use desktop app
2. Open `workflow_diagram.drawio`
3. Drag and rearrange elements as needed
4. Export to PNG, SVG, PDF, or other formats

**Pros:**
- Full visual editor
- Easy drag-and-drop repositioning
- Export to any format
- No installation required (web-based)

### 2. Mermaid (Best for Documentation)
**File:** `workflow_diagram.mmd`

Markdown-compatible diagram format that renders in GitHub, VS Code, and many documentation tools.

**How to use:**
```bash
# Install Mermaid CLI (optional)
npm install -g @mermaid-js/mermaid-cli

# Generate PNG from .mmd file
mmdc -i workflow_diagram.mmd -o workflow_diagram_mermaid.png

# Or view in VS Code with Mermaid extension
# Or paste into GitHub markdown files
```

**Preview online:** [Mermaid Live Editor](https://mermaid.live/)

**Pros:**
- Text-based (easy version control)
- Renders directly in GitHub/GitLab
- Editable in any text editor
- Great for documentation

### 3. PlantUML (Best for Technical Diagrams)
**File:** `workflow_diagram.puml`

Text-based UML diagram format with rich features for technical diagrams.

**How to use:**
```bash
# Install PlantUML (requires Java)
brew install plantuml  # macOS
# or download from https://plantuml.com/

# Generate PNG from .puml file
plantuml workflow_diagram.puml

# Or use online editor
```

**Preview online:** [PlantUML Online Editor](http://www.plantuml.com/plantuml/uml/)

**Pros:**
- Text-based (version control friendly)
- Rich UML feature set
- Professional output
- Widely supported

### 4. Python/Graphviz (Current PNG Generator)
**File:** `generate_workflow_diagram.py`

Programmatic generation using Python and Graphviz library.

**How to use:**
```bash
cd Utils
python3 generate_workflow_diagram.py
# Generates: workflow_diagram.png
```

**Pros:**
- Automated generation
- Scriptable and repeatable
- Professional process flow shapes

**Cons:**
- Less flexible for manual layout adjustments
- Requires Python + Graphviz installation

## 🎯 Recommended Workflow

**For Manual Layout Adjustments (matching your screenshot):**

1. **Start with Draw.io** - Most visual and flexible
   - Open `workflow_diagram.drawio` in [app.diagrams.net](https://app.diagrams.net/)
   - Drag nodes to match exact layout from screenshot
   - Adjust phase box positions vertically
   - Fine-tune Memory Management Protocol position on the right
   - Export to PNG/SVG when satisfied

2. **Or use Mermaid** - If you prefer text editing
   - Edit `workflow_diagram.mmd` in any text editor
   - Adjust `direction LR` within subgraphs for horizontal flow
   - Preview changes in real-time with Mermaid Live Editor
   - Commit to Git (text-based, version control friendly)

3. **Or use PlantUML** - For activity diagram style
   - Edit `workflow_diagram.puml` in text editor
   - Use partition blocks for phase grouping
   - Preview online at plantuml.com
   - Generate high-quality output

## 🎯 Purpose

The workflow diagram illustrates the complete development process from initial concept to deployment:

1. **PRD Development** - Iterative 4-round process using `PRD_DevelopmentPrompt.md`
2. **Task Generation** - Converting PRD into executable `tasks.md` using `Task List Generator.md`
3. **Iterative Development** - Claude Code agent executing tasks with strategic context management
4. **Memory Management** - Optimal use of `/clear`, `/context`, `/compact` commands

## 🚀 Quick Start

### High-Level Diagram (Recommended Starting Point)

**For presentations, documentation, or executive overview:**

```bash
# Generate PNG
cd Utils
python3 workflow_diagram_highlevel.py
# Output: workflow_diagram_highlevel.png
```

Or open `workflow_diagram_highlevel.drawio` in [app.diagrams.net](https://app.diagrams.net/) for manual editing.

**Features:**
- ✅ Simple left-to-right flow
- ✅ 5 main phases clearly visible
- ✅ No internal complexity
- ✅ Perfect for high-level communication

---

### Detailed Diagram (Full Process View)

**For development teams, technical documentation:**

### Option 1: Draw.io (No Installation Required)

1. Go to [app.diagrams.net](https://app.diagrams.net/)
2. Click "Open Existing Diagram"
3. Select `workflow_diagram.drawio` from this directory
4. Edit and arrange as needed
5. Export to your desired format (PNG, SVG, PDF)

### Option 2: Mermaid (Text-Based)

1. Open `workflow_diagram.mmd` in any text editor
2. Edit the Mermaid syntax
3. Preview at [mermaid.live](https://mermaid.live/)
4. Or render directly in VS Code with Mermaid extension

### Option 3: PlantUML (Text-Based)

1. Install PlantUML: `brew install plantuml` (macOS)
2. Edit `workflow_diagram.puml` in any text editor
3. Generate: `plantuml workflow_diagram.puml`
4. Or preview online at [plantuml.com](http://www.plantuml.com/plantuml/uml/)

### Option 4: Python/Graphviz (Programmatic)

**Prerequisites:**
```bash
# Install system Graphviz
brew install graphviz  # macOS
# sudo apt-get install graphviz  # Ubuntu/Debian

# Install Python dependencies
pip install -r requirements.txt
```

**Generate:**
```bash
cd Utils
python3 generate_workflow_diagram.py
```

**Output:** `workflow_diagram.png`

## 📊 Diagram Structure

The diagram uses **landscape orientation (left-to-right flow)** with proper **process flow diagram shapes**:

**Shape Legend:**
- **Ellipses** - Start/End terminal points
- **Rectangles** - Process steps
- **Diamonds** - Decision points
- **Parallelograms** - Documents/Input-Output operations
- **Hexagons** - Parallel execution
- **Notes** - File outputs (PRD.md, tasks.md)
- **Color-coded clusters** - Visual phase separation

### Phase 1: PRD Development
- **Input:** Project concept (ellipse)
- **Process:** 4 iterative rounds with stakeholder consultation (rectangles)
  - Round 1: Foundation Setting (personas, user journeys, AWS services)
  - Round 2: Technical Deep Dive (infrastructure, data flows, APIs)
  - Round 3: Implementation Planning (deployment, testing, monitoring)
  - Round 4: Claude Code Optimization (task decomposition, parallel execution)
- **Output:** Complete PRD.md (note shape)
- **Duration:** Multiple days of refinement recommended

### Phase 2: Task Generation
- **Input:** PRD.md
- **Process:**
  - Analyze requirements
  - Decompose into hierarchical tasks (1.1, 1.2.1, etc.)
  - Map dependencies and parallel work opportunities
  - Add verification criteria
- **Output:** tasks.md with `[pending]` status markers

### Phase 3: Iterative Development
- **Context Management Cycle:**
  1. `/clear` - Reset Claude Code context
  2. Load foundational documents (CLAUDE.md, README.md, .env)
  3. Read tasks.md for current work
  4. Execute tasks (parallel when independent)
  5. Mark status: `[pending]` → `[in-progress]` → `[completed]`

- **Refresh Triggers:**
  - After completing each major phase
  - Within phase for complex tasks or errors
  - When context exceeds 80% capacity
  - After rate limits or interruptions

### Memory Management
Key commands for optimal performance:
- `/clear` - Complete context reset
- `/context` - View current context usage
- `/compact` - Compress conversation history
- `/resume` - Continue interrupted work

**Performance Impact:** 39% improvement with strategic memory management (per README.md)

## 🔧 Customization

### Modifying the Diagram

Edit `generate_workflow_diagram.py` to adjust:

**Layout & Orientation:**
```python
dot.attr(rankdir='LR', splines='ortho', nodesep='0.6', ranksep='1.2')
# rankdir: 'TB'=top-bottom, 'LR'=left-right, 'RL'=right-left, 'BT'=bottom-top
# splines: 'ortho'=orthogonal, 'spline'=curved, 'line'=straight, 'polyline'=piecewise
```

**Node Shapes & Colors:**
```python
dot.node('node_id', 'Label Text',
         shape='box',              # box, diamond, ellipse, parallelogram, hexagon, note, cylinder
         fillcolor='#2E86AB',      # Hex color code
         fontcolor='white',        # Text color
         width='1.5')              # Node width
```

**Edge Styles:**
```python
dot.edge('from_node', 'to_node',
         label='Label Text',       # Edge label
         color='#6A994E',         # Edge color
         penwidth='2',            # Line thickness
         style='solid')           # solid, dashed, dotted, bold
```

**Output Format:**
```python
dot.render('workflow_diagram', format='png', cleanup=True)
# format: 'png', 'svg', 'pdf', 'jpg'
```

### Node Shape Reference

```python
# Common flowchart shapes:
shape='ellipse'         # Start/End terminals
shape='box'             # Process steps
shape='diamond'         # Decision points
shape='parallelogram'   # Input/Output, Documents
shape='hexagon'         # Parallel processing
shape='cylinder'        # Database/Storage
shape='note'            # Document/File outputs
shape='trapezium'       # Manual operations
```

### Adding New Elements

```python
# Add a new node to an existing subgraph
with dot.subgraph(name='cluster_0') as phase1:
    phase1.node('new_node', 'New Step\nDescription',
                shape='box', fillcolor='#C73E1D', fontcolor='white')

# Connect nodes with an edge
dot.edge('existing_node', 'new_node', label='Connection', color='#2E86AB')
```

## 📚 Related Documentation

- `../PRD_DevelopmentPrompt.md` - Interactive PRD creation guide
- `../Task List Generator.md` - PRD to tasks.md conversion prompt
- `../README.md` - Main repository documentation
- `../CLAUDE.md` - Project-specific instructions template

## 🛠️ Troubleshooting

### "graphviz executable not found"
```bash
# Install system Graphviz
brew install graphviz  # macOS
sudo apt-get install graphviz  # Linux

# Verify PATH includes Graphviz
echo $PATH | grep graphviz
```

### "No module named 'graphviz'"
```bash
# Install Python dependencies
pip install -r requirements.txt

# Or install directly
pip install graphviz==0.20.3
```

### Diagram appears cluttered
- Adjust `nodesep` and `ranksep` in dot.attr()
- Change `splines` from "ortho" to "spline" for curved lines
- Increase `ranksep` for more horizontal spacing between phases

### Edge labels not displaying properly
If you see warnings about orthogonal edges and labels:
- Use `xlabel` instead of `label` for edge labels with ortho splines
- Or change to `splines='spline'` for curved edges that handle labels better

### Need different output format
```python
# In generate_workflow_diagram.py
dot.render('workflow_diagram', format='svg', cleanup=True)  # Vector format, scalable
dot.render('workflow_diagram', format='pdf', cleanup=True)  # For printing
dot.render('workflow_diagram', format='jpg', cleanup=True)  # JPEG image
```

## 🤝 Contributing

When updating the workflow diagram:

1. Modify `generate_workflow_diagram.py`
2. Regenerate: `python generate_workflow_diagram.py`
3. Verify visual output
4. Update this README if adding new features
5. Commit both script and generated diagram

## 📝 Notes

- **Professional Flowchart Design**: Uses standard process flow diagram shapes (not emoji)
- **Shape Semantics**:
  - Ellipses = Start/End points
  - Rectangles = Process steps
  - Diamonds = Decision points
  - Parallelograms = Input/Output operations
  - Hexagons = Parallel execution
  - Notes = Document/File outputs
- **Color Coding**: Each phase has distinct colors for visual hierarchy
- **Edge Styles**:
  - Solid lines = Primary flow
  - Dashed lines = Feedback/iteration loops
  - Thicker lines = Critical paths
- **Landscape Orientation**: Left-to-right flow for better readability
- **Output Size**: ~2000-3000px wide for clarity and detail

## 🔗 References

- [Graphviz Official Documentation](https://graphviz.org/documentation/)
- [Graphviz Python Library](https://graphviz.readthedocs.io/en/stable/)
- [Graphviz Node Shapes Reference](https://www.graphviz.org/doc/info/shapes.html)
- [Graphviz Attributes Reference](https://www.graphviz.org/doc/info/attrs.html)
- [Process Flow Diagram Standards](https://en.wikipedia.org/wiki/Flowchart)
