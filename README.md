# Weather MCP Server

A Model Context Protocol (MCP) server that provides real-time weather data to Claude Code and other MCP-compatible AI clients.

## Step 1 — Build and Run the MCP Server

```bash
docker build -t weather-mcp .
docker run -d -p 8000:8000 weather-mcp
```

## Step 2 — Add the MCP to Claude Code

```bash
claude mcp add --transport sse weather-mcp http://localhost:8000/sse
```

Replace `localhost` with your server's IP or hostname if running remotely.

## Step 3 — Verify It Was Added

```bash
claude mcp list
```

You should see `weather-mcp` listed with its SSE URL.

## Option 2 — Share with Your Team via `.mcp.json`

Create a `.mcp.json` at your project root and commit it to git:

```json
{
  "mcpServers": {
    "weather-mcp": {
      "type": "sse",
      "url": "http://localhost:8000/sse"
    }
  }
}
```

Update the URL to match your server's address.

## Step 4 — Demo Flow

```bash
# 1. Start the container
docker run -p 8000:8000 weather-mcp

# 2. Register with Claude Code (one-time)
claude mcp add --transport sse weather-mcp http://localhost:8000/sse

# 3. Start a session — tools are now available
claude
```

Then ask naturally:

- "What's the weather in Tokyo?"
- "Compare Paris and Montreal"

Claude Code will call the MCP weather tools automatically.
