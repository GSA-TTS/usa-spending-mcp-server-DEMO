# USA Spending MCP Server

⚠️ **DISCLAIMER: This is a proof of concept and is not intended for production use.**

An MCP server for interacting with the USAspending.gov API, with optional login.gov authentication for cloud deployment.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Installation

### Quick Install

```sh
uv tool install git+https://github.com/GSA-TTS/usa-spending-mcp-server
```

### Development Setup

```sh
git clone https://github.com/GSA-TTS/usa-spending-mcp-server
cd usa-spending-mcp-server
uv sync --dev
```

## Running Modes

The server supports two modes:

| Mode | Command | Use Case |
|------|---------|----------|
| **stdio** | `usa-spending-mcp-server` | Local use with Claude Desktop |
| **HTTP** | `usa-spending-mcp-server-http` | Cloud deployment with login.gov auth |

## Local Setup (Claude Desktop)

1. Get the installed tool path:
   ```sh
   which usa-spending-mcp-server
   ```

2. Add to your Claude MCP config (`~/.claude/claude_desktop_config.json`):
   ```json
   {
     "mcpServers": {
       "usa-spending": {
         "command": "/path/to/usa-spending-mcp-server"
       }
     }
   }
   ```

## HTTP Server with Login.gov Authentication

The HTTP server uses login.gov OIDC with PKCE for authentication, suitable for cloud.gov deployment.

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `REQUIRE_AUTH` | No | Set to `"false"` to disable auth (default: `"true"`) |
| `BASE_URL` | If auth enabled | Public URL of the server (e.g., `https://usa-spending-mcp.app.cloud.gov`) |
| `LOGINGOV_CLIENT_ID` | If auth enabled | Your login.gov application client ID |
| `JWT_SIGNING_KEY` | If auth enabled | Secret key for signing JWTs (generate with `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `LOGINGOV_CONFIG_URL` | No | OIDC discovery URL (defaults to login.gov sandbox) |
| `PORT` | No | Server port (default: `8080`) |

### Login.gov Setup

1. Register at [partners.login.gov](https://partners.login.gov/)
2. Create a new OIDC application:
   - **Protocol**: OpenID Connect with PKCE (public client)
   - **Redirect URI**: `{BASE_URL}/auth/callback`
3. Note your client ID for `LOGINGOV_CLIENT_ID`

### Running Locally

**Without authentication (development):**
```sh
uv run task dev
```

**With authentication:**
```sh
export BASE_URL=http://localhost:8080
export LOGINGOV_CLIENT_ID=your-client-id
export JWT_SIGNING_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
uv run task dev-auth
```

## Cloud.gov Deployment

1. Set environment variables:
   ```sh
   cf set-env usa-spending-mcp-server BASE_URL https://usa-spending-mcp.app.cloud.gov
   cf set-env usa-spending-mcp-server LOGINGOV_CLIENT_ID your-client-id
   cf set-env usa-spending-mcp-server JWT_SIGNING_KEY your-signing-key
   ```

2. Deploy:
   ```sh
   cf push
   ```

## Development

### Available Tasks

```sh
uv run task dev          # Run HTTP server without auth
uv run task dev-auth     # Run HTTP server with auth
uv run task lint         # Check code with ruff
uv run task lint-fix     # Fix linting issues
uv run task format       # Format code with ruff
uv run task test         # Run tests
uv run task test-cov     # Run tests with coverage
uv run task ci           # Run all CI checks
```

### Code Quality

This project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting.

## LLM-Based Evals (Optional)

For local testing of tool behavior using [mcp-evals](https://github.com/mclenhard/mcp-evals):

```sh
cd evals
npm install
ANTHROPIC_API_KEY=your-key npm run eval
```

See `evals/README.md` for details.

## Project Structure

```
src/
  usa_spending_mcp_server/
    server.py        # stdio MCP server (Claude Desktop)
    server_http.py   # HTTP server with auth (cloud.gov)
    auth.py          # login.gov OIDC authentication
tests/               # Python unit tests
evals/               # LLM-based evals (optional)
manifest.yml         # cloud.gov deployment config
pyproject.toml
```