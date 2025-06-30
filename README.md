# USA Spending MCP Server

A simple MCP server for interacting with the USAspending.gov API.

## Requirements

- Python 3.13+
- [Poetry](https://python-poetry.org/)

## Setup

1. **Install dependencies:**

   ```sh
   poetry install
   ```

2. **Activate the virtual environment:**

   ```sh
   poetry env activate
   ```

## Simple way to connect to Claude 
1. Get path 
   ```sh
   ➜  usa-spending-mcp-server git:(feature/award_spending) poetry run which usa-spending-mcp-server
   /Users/samuellevy/Library/Caches/pypoetry/virtualenvs/usa-spending-mcp-server-4uFFGwlz-py3.13/bin/usa-spending-mcp-server
   ```
2. Copy path into Claude MCP config
   ```
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
3. Anytime you need to update mcp server rerun
   ```sh
   poetry install
   ```  
## Running the Server

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
