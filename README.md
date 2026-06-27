# MCP (Model Context Protocol) Theory

## Overview

The **Model Context Protocol (MCP)** is an open protocol developed by Anthropic that standardizes how applications provide context and tools to Large Language Models (LLMs). Think of MCP as a "USB-C port for AI applications" — a universal interface that connects AI models with external data sources, tools, and services.

## Core Concepts

### 1. **Hosts**
Hosts are applications (like Claude Desktop, IDEs, or custom UIs) that initiate connections to MCP servers. They are responsible for:
- Establishing connections to MCP servers
- Managing authentication and authorization
- Presenting information to the user
- Coordinating multiple server interactions

### 2. **Servers**
MCP servers are lightweight programs that expose specific capabilities through the MCP protocol. Each server provides:
- **Resources**: Data that can be read (like files, database records, API responses)
- **Tools**: Functions that LLMs can call (like search, calculation, data manipulation)
- **Prompts**: Pre-written templates for common tasks

### 3. **Clients (Contexts)**
Clients are protocol clients that maintain a 1:1 connection with servers. They are created by hosts and handle:
- Sending requests and receiving responses
- Managing state and context
- Handling streaming responses

## Communication Protocol

MCP uses **JSON-RPC 2.0** as its wire format, running over either:
- **stdio** (standard input/output) — for local, subprocess-based communication
- **SSE** (Server-Sent Events) over HTTP — for remote network-based communication

### Message Types

| Type | Direction | Purpose |
|------|-----------|---------|
| Request | Client → Server | Initiate an operation |
| Response | Server → Client | Return results of an operation |
| Notification | Either direction | Event-driven messages (no response expected) |

## Capabilities

### Resources
File-like data that can be accessed by LLMs:
- Static resources (constant data)
- Dynamic resources (computed on access)
- Directory listings (resource templates)
- Resource subscriptions (change notifications)

### Tools
Functions that LLMs can discover and invoke:
- Named with descriptions
- Type-safe parameters (JSON Schema)
- Optional result streaming
- Error handling with structured responses

### Prompts
Reusable prompt templates:
- Parameterized text templates
- Dynamic argument resolution
- Multi-message support
- Context injection

## Lifecycle

1. **Initialization**: Client and server exchange capabilities and negotiate protocol version
2. **Operation**: Normal operation with resource access, tool calls, and prompt retrieval
3. **Shutdown**: Graceful termination of the connection

## Security Model

- Users approve tool invocations (human-in-the-loop)
- Servers run in isolated environments
- No direct network access from LLM — all I/O goes through MCP protocol
- Resource access is governed by server implementation

## Benefits

- **Interoperability**: Any MCP-compatible client can use any MCP server
- **Discoverability**: Clients can dynamically discover available tools and resources
- **Type Safety**: Structured schemas for parameters and return values
- **Standardization**: One protocol for all AI-tool integrations
- **Security**: Controlled, auditable access between models and data

## Common Use Cases

- Database querying and management
- File system operations
- API integrations
- Code analysis and repository management
- Web scraping and data extraction
- DevOps and infrastructure management
- Knowledge base retrieval (RAG)

---

*MCP is an open standard. For the latest specification, visit [modelcontextprotocol.io](https://modelcontextprotocol.io)*
