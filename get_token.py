#!/usr/bin/env python3
"""
Obtain access token from Microsoft Entra Id using device code flow
"""

import os
import sys
import logging
import msal
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Azure Entra ID configuration
TENANT_ID = os.getenv("TENANT_ID")  # Tenant ID from environment
WEB_CLIENT_ID = os.getenv("WEB_CLIENT_ID")  # Client ID from environment
API_CLIENT_ID = os.getenv("API_CLIENT_ID")  # Client ID for API

# check if required environment variables are set
if not TENANT_ID or not API_CLIENT_ID or not WEB_CLIENT_ID:
    raise ValueError("TENANT_ID, API_CLIENT_ID, and WEB_CLIENT_ID must be set in the environment variables")

API_SCOPE = f"api://{API_CLIENT_ID}/execute"  # API scope
API_AUDIENCE = f"api://{API_CLIENT_ID}"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"


def get_token():
    """Get an access token for the API"""
    
    # Create MSAL app
    app = msal.PublicClientApplication(
        client_id=WEB_CLIENT_ID,
        authority=AUTHORITY
    )
        
    # Acquire token interactively
    flow_started = app.initiate_device_flow(scopes=[API_SCOPE])
    if "user_code" not in flow_started:
        logger.error(f"Failed to create device flow: {flow_started.get('error')}")
        logger.error(f"Error description: {flow_started.get('error_description')}")
        return None
    
    # Display instructions to user
    logger.info(flow_started["message"])
    
    # Poll for token
    result = app.acquire_token_by_device_flow(flow_started)
    
    return result


def get_jwt_token():
    """
    Get just the JWT token string for programmatic use.
    
    Returns:
        str: The access token string, or None if acquisition fails
    """
    result = get_token()
    if "access_token" in result:
        return result["access_token"]
    else:
        logger.error(f"Failed to obtain token: {result.get('error')}")
        logger.error(f"Error description: {result.get('error_description')}")
        return None
    

def main() -> int:
    token = get_jwt_token()
    if not token:
        logger.error("Failed to get JWT token")
        return
        
    logger.info("Successfully obtained JWT token")
    logger.info(f"JWT Token: {token}")

if __name__ == '__main__':
    sys.exit(main()) 