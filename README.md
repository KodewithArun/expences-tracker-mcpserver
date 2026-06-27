# Simple Remote Server

A simple calculator MCP server built with [FastMCP](https://github.com/jlowin/fastmcp). Exposes basic arithmetic operations as tools via the Model Context Protocol.

## Tools

| Tool | Description |
|------|-------------|
| `add(a, b)` | Returns a + b |
| `subtract(a, b)` | Returns a - b |
| `multiply(a, b)` | Returns a * b |
| `divide(a, b)` | Returns a / b |
| `hello(name)` | Returns a greeting |

## Resource

- `info://simpleremoteserver` — Server metadata

## Usage

```bash
# Install dependencies
uv sync

# Run the server
python main.py
```

The server starts on `http://0.0.0.0:8080/mcp`.
