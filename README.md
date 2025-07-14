# USA Spending MCP Server

⚠️ **DISCLAIMER: This is a proof of concept and is not intended for production use.**

A simple MCP server for interacting with the USAspending.gov API.

## Requirements

- Python 3.13+
- [Poetry](https://python-poetry.org/) OR [uv](https://docs.astral.sh/uv/)

## Installation Options

### Option 1: Install via uv (Recommended for quick setup)

```sh
uv tool install git+https://github.com/GSA-TTS/arc-usa-spending-mcp-server
```

### Option 2: Development Setup with Poetry

1. **Install dependencies:**

   ```sh
   poetry install
   ```

2. **Activate the virtual environment:**

   ```sh
   poetry env activate
   ```

## Simple way to connect to Claude 

### For uv installation:
1. Get the installed tool path:
   ```sh
   which usa-spending-mcp-server
   ```

2. Copy the path into Claude MCP config:
   ```json
   {
     "mcpServers": {
       "usa-spending": {
         "command": "/path/to/usa-spending-mcp-server",
         "args": [],
         "env": {}
       }
     }
   }
   ```

### For Poetry development setup:
1. Get path:
   ```sh
   ➜  usa-spending-mcp-server git:(feature/award_spending) poetry run which usa-spending-mcp-server
   /Users/samuellevy/Library/Caches/pypoetry/virtualenvs/usa-spending-mcp-server-4uFFGwlz-py3.13/bin/usa-spending-mcp-server
   ```

2. Copy path into Claude MCP config:
   ```json
   {
     "mcpServers": {
       "usa-spending": {
         "command": "/Users/samuellevy/Library/Caches/pypoetry/virtualenvs/usa-spending-mcp-server-4uFFGwlz-py3.13/bin/usa-spending-mcp-server",
         "args": [],
         "env": {}
       }
     }
   }
   ```

3. Anytime you need to update mcp server rerun:
   ```sh
   poetry install
   ```  

## Running the Server

### With uv:
```sh
usa-spending-mcp-server
```

### With Poetry:
```sh
poetry run usa-spending-mcp-server
```

## Code Formatting

This project uses [black](https://black.readthedocs.io/en/stable/) and [isort](https://pycqa.github.io/isort/) for code formatting and import sorting.

- **Format code with black:**

  ```sh
  poetry run black .
  ```

- **Sort imports with isort:**

  ```sh
  poetry run isort .
  ```

## Project Structure

```
src/
  usa_spending_mcp_server/
tests/
pyproject.toml
README.md
```