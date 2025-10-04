# Setup Azure App Registrations

For this project to work, you need two Entra Id (Azure AD) App Registrations.

1. For the Client that will call the MCP Server (In this case a python script, but imagine for example a Web Interface with SSO).
2. For the MCP Server that will call the Microsoft Graph API on behalf of the User (The user who is logged in at the Client)

## App Registration for Client

This one is really simple as the python scripts in this project obtain the access token using the device code flow and don't access any other resources.

- Name: FastMCP Auth Web
- Allow public client flows: yes

Write the Directory (tenant) ID to `TENANT_ID` in the .env file.
Write the Application (client) ID to `WEB_CLIENT_ID` in the .env file.


## App Registration for MCP Server

This one will need a client secret and permissions to access Graph API Resources. In this case the `User.Read` Permission is enough to get the logged in user.
It will also have to expose an API so the Client application can exchange the users token for a token valid for this second App registration.

- Name: FastMCP Auth API
- Scopes: api://<Client Id of this App Registration>/execute (/execute is actually arbitrary, it just has to match the scope in the request from the client)
- Authorized client applications: The Client Id of the first App registration. 
    - Authorized scopes for that must be the `execute` scope


Write the Application (client) ID to `API_CLIENT_ID` in the .env file.
Write the client secret value to `CLIENT_SECRET` in the .env file.
