#!/usr/bin/env python3
"""
Simple MCP Server with with Azure Entra ID Authentication and OBO flow for Microsoft Search
"""

import logging
import os
from dotenv import load_dotenv
from fastmcp import FastMCP, Context
from fastmcp.server.auth import BearerAuthProvider
from fastmcp.server.dependencies import get_access_token, AccessToken
import asyncio
import random
import requests
import jwt
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import json

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Azure Entra ID configuration
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("API_CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# Check the required environment variables
if not TENANT_ID or not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("TENANT_ID, CLIENT_ID, and CLIENT_SECRET must be set in the environment variables")

# API audience
API_AUDIENCE = f"api://{CLIENT_ID}"

# Azure Entra ID JWKS endpoint
JWKS_URI = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"

# Configure Bearer Token authentication for Azure Entra ID
logger.info("Configuring Bearer Token authentication with audience: %s", API_AUDIENCE)
auth = BearerAuthProvider(
    jwks_uri=JWKS_URI,
    issuer=f"https://sts.windows.net/{TENANT_ID}/",  # Match the token's issuer format in the API
    algorithm="RS256",  # Azure Entra ID uses RS256
    audience=API_AUDIENCE,  # required audience
    required_scopes=["execute"]  # Optional: add required scopes if needed
)

# Create the MCP server with authentication
mcp = FastMCP("Simple Reverse Server with Azure Auth", auth=auth)

# Without authentication, just for testing
# mcp = FastMCP("Simple Reverse Server with Azure Auth")

async def exchange_token(original_token: str, scope: str) -> dict:
    """
    Exchange JWT token for downstream service token using OBO flow
    """
    if not CLIENT_SECRET:
        return {
            "success": False,
            "error": "CLIENT_SECRET not configured",
            "method": "OBO"
        }
    
    obo_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    
    data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "assertion": original_token,
        "scope": scope,
        "requested_token_use": "on_behalf_of"
    }
    
    try:
        response = requests.post(obo_url, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            return {
                "success": True,
                "access_token": token_data["access_token"],
                "expires_in": token_data.get("expires_in"),
                "token_type": token_data.get("token_type"),
                "scope_used": scope,
                "method": "OBO"
            }
        else:
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code,
                "scope_attempted": scope,
                "method": "OBO"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "method": "OBO"
        }

def decode_token_info(token: str) -> dict:
    """
    Decode token to show basic info (without verification)
    """
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return {
            "audience": decoded.get("aud"),
            "issuer": decoded.get("iss"),
            "subject": decoded.get("sub"),
            "user_id": decoded.get("oid"),
            "email": decoded.get("email"),
            "scopes": decoded.get("scp"),
            "expires": decoded.get("exp"),
            "roles": decoded.get("roles"),
            "app_id": decoded.get("appid")
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_documents(ctx: Context, query: str = "*") -> dict:
    """
    Retrieve documents from Azure Search using the provided query.
    
    Args:
        ctx: FastMCP context
        query: The search query
        
    Returns:
        list of documents
    """
    logger.info(f"get_documents called with query: {query}")
    # Get the access token from the context
    access_token: AccessToken = get_access_token()
    original_token = access_token.token

    # Exchange token for Microsoft Search token
    logger.info("Exchanging token for Microsoft Search access")
    exchange_token_result = await exchange_token(original_token, scope="https://graph.microsoft.com/.default")
    if not exchange_token_result["success"]:
        return {"error": "Could not retrieve documents due to token exchange failure."}
    else:
        logger.info("Search token exchange successful")
        graph_token = exchange_token_result["access_token"]

        logger.info("Now I am getting all the search results from SharePoint ... not!")

        documents = [
            {
            "name": "New Document",
            "oid": "Some oid",
            "group": "Aaaaand a group"
            }
        ]
        return {"documents": documents}
    
@mcp.tool()
async def get_loggedin_user(ctx: Context) -> dict:
    """
    Retrieve information about the currently logged in user from Microsoft Graph
    
    Args:
        ctx: FastMCP context
        
    Returns:
        - display_name: User's display name
        - email: User's email address (mail or userPrincipalName)
        - user_principal_name: User's UPN
        - id: User's unique identifier
        - job_title: User's job title (if available)
        - office_location: User's office location (if available)
    """
    logger.info("get_loggedin_user called.")
    # Get the access token from the context
    access_token: AccessToken = get_access_token()
    original_token = access_token.token

    # Exchange token for Microsoft Search token
    logger.info("Exchanging token for Microsoft Graph API access")
    exchange_token_result = await exchange_token(original_token, scope="https://graph.microsoft.com/.default")

    if not exchange_token_result["success"]:
        return {"error": "Could not retrieve logged in user due to token exchange failure."}
    else:
        logger.info("Graph API token exchange successful")
        graph_token = exchange_token_result["access_token"]

        headers = {
            'Authorization': f'Bearer {graph_token}',
            'Content-Type': 'application/json'
        }
        
        # Make request to Microsoft Graph /me endpoint
        response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            return {
                'display_name': user_data.get('displayName'),
                'email': user_data.get('mail') or user_data.get('userPrincipalName'),
                'user_principal_name': user_data.get('userPrincipalName'),
                'id': user_data.get('id'),
                'job_title': user_data.get('jobTitle'),
                'office_location': user_data.get('officeLocation')
            }
        else:
            raise Exception(f"Failed to get user profile: {response.status_code} - {response.text}")
    
def main():
    """Main entry point for the FastMCP server"""
    logger.info("Starting authenticated FastMCP server...")
    logger.info(f"Azure Tenant ID: {TENANT_ID}")
    logger.info(f"Azure Client ID: {CLIENT_ID}")
    logger.info(f"JWKS URI: {JWKS_URI}")
    
    try:
        # Run the server with HTTP transport (required for authentication)
        # Authentication only works with HTTP-based transports
        mcp.run(
            transport="streamable-http",  # Use HTTP transport for authentication
            host="0.0.0.0",
            port=8000
        )
    except Exception as e:
        logger.error(f"Error running server: {e}")
        raise


if __name__ == "__main__":
    main()