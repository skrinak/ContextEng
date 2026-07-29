# UV Setup

You generally **don't** "initiate a uv environment with imports." A `uv` virtual environment is a clean, isolated Python environment. You first **create** and **activate** the environment, and *then* you **install** the necessary packages (imports) into it.

The process of initiating the environment and setting up your project's dependencies is a two-step process:

-----

## 1\. Create and Activate the Windows Environment

First, use `uv venv` to create the isolated environment, and then activate it.

| Step | Command | Description |
| :--- | :--- | :--- |
| **Create** | `uv venv .venv` | Creates the virtual environment folder named `.venv`. |
| **Activate** | `source .venv/bin/activate` | **(macOS/Linux)** Activates the environment so subsequent commands install packages into it. |
| **Activate** | `.\.venv\Scripts\Activate.ps1` | **(Windows PowerShell)** Activates the environment. |

-----

## 2\. Install Imports (Packages)

Once activated, you use `uv pip install` to install your project's dependencies (the "imports" your code relies on) into the environment.

### A. Installing from a `requirements.txt` file

This is the standard and best practice for managing project dependencies.

```bash
# Assuming you have a file named 'requirements.txt'
uv pip install -r requirements.txt
```

### B. Installing Individual Packages

You can install packages one by one directly:

```bash
uv pip install requests pandas beautifulsoup4
```

### C. Installing in One Step with a Requirements File

While `uv` doesn't have a single command to create the environment *and* install dependencies simultaneously like some other tools, you can easily combine the steps into a simple script or just execute them sequentially:

```bash
# 1. Create the environment
uv venv .venv

# 2. Activate the environment (using a subshell for simplicity)
source .venv/bin/activate

# 3. Install packages from the requirements file
uv pip install -r requirements.txt
```