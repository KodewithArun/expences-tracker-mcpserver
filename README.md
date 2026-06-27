# Expences Tracker MCP Server

A personal finance tracker powered by **FastMCP** + **SQLite**. Manage expenses and income through any AI assistant that supports the **Model Context Protocol (MCP)**.

## Architecture

```
┌─────────────────────┐     MCP      ┌──────────────────────────┐
│  AI Assistant        │ ◄─────────► │  expences-tracker-mcp    │
│  (opencode, Claude)  │             │  (FastMCP server)        │
└─────────────────────┘             │  ┌──────────────────────┐│
                                      │  │  SQLite (expenses.db)││
                                      │  └──────────────────────┘│
                                      └──────────────────────────┘
```

## Features

| Tool | Description |
|------|-------------|
| `add_category` | Create expense/income categories |
| `list_categories` | Browse all categories |
| `update_category` | Rename or re-type a category |
| `delete_category` | Remove a category (blocked if in use) |
| `add_transaction` | Log an expense or income entry |
| `list_transactions` | Filter by date, category, or type |
| `update_transaction` | Edit any transaction field |
| `delete_transaction` | Remove a transaction by ID |
| `get_summary` | Income/expense summary for a period |
| `get_monthly_report` | Detailed monthly breakdown |

## What I Learned

- **MCP (Model Context Protocol)** — a standardized way for AI assistants to interact with tools and data sources.
- **FastMCP** — a Python framework for building MCP servers with minimal boilerplate.
- **SQLite** — embedded database for local-first data persistence.
- **Tool-based interaction** — each operation (CRUD on categories & transactions, reporting) is exposed as a typed tool the AI can call.
- **Local MCP deployment** — the server runs locally via `uv`/`python` and is registered in `opencode.json` for use with opencode.

## Usage

The server is registered in `opencode.json`. Just ask your AI:

> "Add lunch expense of ₹450 under Food & Drink"  
> "Show me this month's summary"  
> "Delete transaction #3"

## Setup

```bash
uv sync
python main.py
```
