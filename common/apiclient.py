import os
import time
import requests
from typing import Optional


class ApiClient:
        
    def __init__(self, client_id: str, client_secret: str, token_url: str, api_base_url: str):
        # self.client_id = os.environ.get("COGNITO_CLIENT_ID")
        # self.client_secret = os.environ.get("COGNITO_CLIENT_SECRET")
        # self.token_url = os.environ.get("COGNITO_TOKEN_URL")  # e.g., https://your-domain.auth.us-west-2.amazoncognito.com/oauth2/token

        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url

        # if not all([self.client_id, self.client_secret, self.token_url]):
        #     raise EnvironmentError("Missing one or more required environment variables: COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET, COGNITO_TOKEN_URL")

        self.api_base_url = api_base_url.rstrip("/")  # e.g., https://api.example.com
        self.access_token: Optional[str] = None
        self.token_expiry = 0

    def _get_access_token(self) -> str:
        #*** Some how cache token not working throw 403 forbidden error***
        # if self.access_token and time.time() < self.token_expiry - 60:
        #     return self.access_token

        data = {
            "grant_type": "client_credentials"
        }

        auth = (self.client_id, self.client_secret)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = requests.post(self.token_url, data=data, headers=headers, auth=auth)

        if response.status_code != 200:
            raise Exception(f"Failed to get token: {response.status_code} - {response.text}")

        token_data = response.json()
        self.access_token = token_data["access_token"]
        self.token_expiry = time.time() + token_data.get("expires_in", 3600)

        return self.access_token

    async def call_api(self, method: str, path: str, params=None, data=None, json=None, headers=None):
        url = f"{self.api_base_url}/{path.lstrip('/')}"
        print(f'{method} {path} json:{json}')
        token = self._get_access_token()
        req_headers = headers.copy() if headers else {}
        req_headers["Authorization"] = f"Bearer {token}"
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=req_headers,
            params=params,
            data=data,
            json=json
        )

        if not response.ok:
            raise Exception(f"API call failed: {response.status_code} - {response.text}")
        print(f'{method} {path} ==> http {response.status_code}')
        return response

    async def call_api_unified(self, method: str, path_or_url: str, token_key: str = "Authorization", token: Optional[str] = None, params=None, data=None, json=None, headers=None):
        """
        Unified API call method that handles both internal API calls (using path) and external API calls (using full URL).
        
        For internal API calls:
        - Provide path (e.g., "/api/sessions/123")
        - Token will be automatically acquired from token_url if not provided
        
        For external API calls:
        - Provide full URL (e.g., "https://external-api.com/orders")
        - Token is optional - provide token_key (e.g., "Authorization", "X-API-Key") and token if authentication is required
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path_or_url: Either a path (for internal API) or full URL (for external API)
            token_key: Header key for token (default: "Authorization") - only used if token is provided
            token: Token value. If None for internal calls, will auto-acquire from token_url. Optional for external calls.
            params, data, json, headers: Standard request parameters
        """
        print(f'base url: {self.api_base_url}, path_or_url: {path_or_url}') 
        # Determine if this is an internal API call (path) or external (full URL)
        if path_or_url.startswith(('http://', 'https://')):
            # External API call - use provided URL directly
            url = path_or_url
            # For external calls, token is optional
        else:
            # Internal API call - construct URL from base_url + path
            url = f"{self.api_base_url}/{path_or_url.lstrip('/')}"
            print(f'Internal API call, constructed URL: {url}')
            # For internal calls, acquire token if not provided
            if token is None:
                token = self._get_access_token()
                token_key = "Authorization"
                token = f"Bearer {token}"
        
        # print(f'Method: {method} URL/PATH: {path_or_url} json:{json}')
        
        req_headers = headers.copy() if headers else {}
        if token is not None:
            req_headers[token_key] = token
        
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=req_headers,
            params=params,
            data=data,
            json=json
        )

        if not response.ok:
            raise Exception(f"API call failed: {response.status_code} - {response.text}")
        print(f'{method} {path_or_url} ==> http {response.status_code}')
        return response
        
