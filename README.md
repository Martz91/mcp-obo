# On-behalf-of flow with Entra ID and FastMCP

This is a Fork of gbaeke`s implementation that uses the Microsoft Graph /me Endpoind instead of AI Search to make the sample a bit more accessible.

Blog post for the original implementation: https://baeke.info/2025/07/29/end-to-end-authorization-with-entra-id-and-mcp/

## Instructions

### 1. Create and activate a Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file in the project root with the required Azure and API credentials (see example files for required variables).
See `AZURE_SETUP.md` for instructions on how to setup the Azure AD App Registrations.

### 4. Start the MCP server

```bash
python mcp/main.py
```

### 5. Run the MCP client

In a new terminal (with the virtual environment activated):

```bash
python mcp_client.py
```

### 6. Configure the MCP server in VSCode (to use with Github Copilot)

Open the file `.vscode/mcp.json` in VSCode. The MCP Server is defined in there already. Replace `<Entra Id Token>` with your Entra Id Access token.
To obtain the token you can use `python get_token.py`.

As long as the token is valid, Copilot can use the MCP Server in Agent Mode.

## Diagrams

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant Client
    participant AzureAD as "Azure Entra ID"
    participant MCP
    participant MSGraph

    User->>Client: Initiate Device Flow
    Client->>AzureAD: Start Device Code Flow
    AzureAD-->>Client: Device Code + Verification URL
    Client->>User: Show Code + URL

    User->>AzureAD: Authenticates via browser
    AzureAD-->>Client: Returns Access Token (for MCP)

    Client->>MCP: Call tool with Bearer Access Token
    MCP->>AzureAD: OBO request for token to call MS Graph\n(include access token as assertion)
    AzureAD-->>MCP: Returns new Access Token (for MS Graph)

    MCP->>MSGraph: Call Graph API with new token
    MSGraph-->>MCP: Graph data
    MCP-->>Client: Return tool result
```