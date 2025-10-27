# CoreSignal MCP Server Setup

## Overview

The CoreSignal MCP (Model Context Protocol) server has been configured to provide direct access to CoreSignal's data APIs through Claude Code. This enables AI-powered queries and data retrieval without writing custom API integration code.

## What is CoreSignal MCP?

CoreSignal MCP is a remote server that connects CoreSignal's professional data directly with LLM-powered applications. It provides three primary data sources:

- **coresignal_company_multisource_api** – Multi-source company information
- **coresignal_employee_multisource_api** – Multi-source employee data
- **coresignal_job_api** – Base job listings data

## Configuration

**IMPORTANT:** This is configured for **Claude Code** (VS Code extension), not Claude Desktop app.

The MCP server has been configured in `.mcp.json` at the project root:

```json
{
  "mcpServers": {
    "coresignal": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-remote",
        "https://mcp.coresignal.com/mcp",
        "--header",
        "Authorization: Bearer <YOUR_API_KEY>"
      ]
    }
  }
}
```

## Authentication Setup

### Configuration Complete ✅

The CoreSignal API key from your `backend/.env` file has been configured in `.mcp.json`.

### Next Step: Reload Claude Code Window

Press `Cmd+Shift+P` (macOS) → Type "Reload Window" → Press Enter

The MCP server should be available immediately after reload.

## Usage

Once configured and restarted, you can use natural language queries in Claude Code to:

- Search for employee/professional profiles
- Retrieve company information and intelligence
- Query job listings and market data
- Cross-reference data across multiple sources

Example queries:
- "Find employees at OpenAI with machine learning experience"
- "Get company information for Series A startups in San Francisco"
- "Show recent job postings for senior engineers in fintech"

## Important Notes

1. **Credits Usage**: All requests made through the MCP server will deduct credits from your CoreSignal account balance.

2. **Comparison with Existing Integration**:
   - This project already has direct CoreSignal API integration in `backend/coresignal_service.py`
   - The MCP server provides an alternative, conversational interface
   - For production workflows, continue using the existing Flask endpoints
   - Use MCP for ad-hoc queries, research, and rapid prototyping

3. **Data Freshness**: The MCP server accesses the same CoreSignal APIs as your backend, so data freshness considerations (like using `generated_headline` over `headline`) still apply.

## Troubleshooting

### MCP Server Not Available

If you don't see CoreSignal tools in Claude Code:

1. Verify the config file exists: `cat .mcp.json` (in project root)
2. Check for typos in the configuration JSON
3. Ensure you reloaded the window: `Cmd+Shift+P` → "Reload Window"
4. Check MCP server status: Type `/mcp` in Claude Code
5. Verify Node.js is installed: `node --version` (required for npx)

### API Key Issues

If authentication fails:
1. Verify your API key at https://dashboard.coresignal.com/
2. Check that the API key in `.mcp.json` matches the one in `backend/.env`
3. Test the API key with existing backend: `cd backend && python3 app.py` and try fetching a profile
4. Make sure the API key is properly formatted in `.mcp.json` (no extra quotes or spaces)

## References

- [CoreSignal MCP Documentation](https://docs.coresignal.com/mcp/coresignal-mcp)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- CoreSignal Dashboard: https://dashboard.coresignal.com/
