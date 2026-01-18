"""
Xbox authentication module for Unfolded Circle integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
import asyncio
from urllib.parse import urlparse, parse_qs
import httpx
from pythonxbox.authentication.manager import AuthenticationManager
from .oauth_server import OAuthCallbackServer

_LOG = logging.getLogger("XBOX_AUTH")

# OAuth redirect URI - Local callback server
# User's custom Azure App must have this URL properly registered
# Port 8765 chosen to avoid conflicts with common ports
OAUTH2_REDIRECT_URI = "http://localhost:8765/callback"
DEFAULT_CALLBACK_PORT = 8765

class XboxAuth:
    def __init__(self, session: httpx.AsyncClient, client_id: str, client_secret: str):
        """
        Initialize Xbox authentication with user-provided Azure App credentials.

        Args:
            session: HTTP client session
            client_id: Azure App Registration Client ID
            client_secret: Azure App Client Secret
        """
        self.session = session
        self.auth_mgr = AuthenticationManager(
            session, client_id, client_secret, OAUTH2_REDIRECT_URI
        )
        self.callback_server = OAuthCallbackServer(port=DEFAULT_CALLBACK_PORT, host="0.0.0.0")
        _LOG.info("XboxAuth initialized with user-provided credentials and local callback server.")

    def generate_auth_url(self) -> str:
        """Generate OAuth authorization URL that redirects to our callback page."""
        auth_url = self.auth_mgr.generate_authorization_url()
        _LOG.info(f"Generated auth URL: {auth_url[:100]}...")
        return auth_url

    async def authenticate_with_oauth(self) -> dict | None:
        """
        Perform complete OAuth authentication flow using local callback server.

        This method:
        1. Starts a temporary local HTTP server
        2. Generates and returns the auth URL for the user to visit
        3. Waits for the OAuth callback with authorization code
        4. Exchanges the code for tokens
        5. Stops the server

        Returns:
            dict with OAuth tokens if successful, None otherwise
        """
        _LOG.info("Starting OAuth authentication flow with local callback server...")
        try:
            # Start the callback server
            await self.callback_server.start()
            _LOG.info("Local callback server started successfully.")

            # Generate auth URL
            auth_url = self.generate_auth_url()
            _LOG.info(f"Auth URL generated: {auth_url[:100]}...")

            # Return the auth URL - the caller will display this to the user
            return {"auth_url": auth_url}

        except Exception as e:
            _LOG.exception(f"Error starting OAuth flow: {e}")
            await self.callback_server.stop()
            return None

    async def wait_for_auth_completion(self, timeout: int = 300) -> dict | None:
        """
        Wait for user to complete authentication and exchange code for tokens.

        Args:
            timeout: Maximum time to wait in seconds (default 5 minutes)

        Returns:
            dict with OAuth tokens if successful, None otherwise
        """
        _LOG.info(f"Waiting for OAuth callback (timeout: {timeout}s)...")
        try:
            # Wait for the authorization code
            auth_code = await self.callback_server.wait_for_code(timeout=timeout)

            if not auth_code:
                _LOG.error("No authorization code received within timeout period.")
                return None

            _LOG.info(f"Authorization code received (length: {len(auth_code)})")

            # Exchange code for tokens
            await self.auth_mgr.request_tokens(auth_code)
            _LOG.info("OAuth2 tokens successfully retrieved.")

            return self.auth_mgr.oauth.model_dump()

        except asyncio.TimeoutError:
            _LOG.error(f"Timeout waiting for authorization code after {timeout} seconds")
            return None
        except Exception as e:
            _LOG.exception(f"Error during token exchange: {e}")
            return None
        finally:
            # Always stop the server
            await self.callback_server.stop()
            _LOG.info("OAuth callback server stopped.")

    async def process_manual_code(self, auth_input: str) -> dict | None:
        """
        Process manually entered authorization code or URL.

        Args:
            auth_input: Either the full redirect URL or just the authorization code

        Returns:
            dict with OAuth tokens if successful, None otherwise
        """
        _LOG.info("Processing manually provided authorization code...")
        try:
            # Stop the callback server since we're doing manual entry
            await self.callback_server.stop()

            if not auth_input or not auth_input.strip():
                _LOG.error("Empty authorization input provided.")
                return None

            auth_input = auth_input.strip()

            # Try to extract code from URL if user pasted full URL
            auth_code = auth_input
            if auth_input.startswith("http") or "code=" in auth_input or "error=" in auth_input:
                _LOG.info("Detected URL or query string, extracting code...")
                try:
                    from urllib.parse import urlparse, parse_qs, unquote

                    # Handle URL-encoded URLs
                    if auth_input.startswith("http%3A"):
                        auth_input = unquote(auth_input)

                    # If it looks like a URL, parse it
                    if auth_input.startswith("http"):
                        parsed = urlparse(auth_input)
                        params = parse_qs(parsed.query)

                        # Check for OAuth error first
                        error = params.get('error', [None])[0]
                        if error:
                            error_desc = params.get('error_description', ['Unknown error'])[0]
                            error_desc = unquote(error_desc)
                            _LOG.error(f"OAuth error from Microsoft: {error} - {error_desc}")

                            # Provide specific guidance based on error
                            if error == "unauthorized_client" and "secret" in error_desc.lower():
                                _LOG.error("SETUP ERROR: Azure App is missing a Client Secret. "
                                          "Go to Azure Portal → Your App → Certificates & secrets → "
                                          "Create a new Client Secret and use its VALUE (not ID).")
                            elif error == "invalid_request":
                                _LOG.error("SETUP ERROR: Invalid redirect URI or app configuration. "
                                          "Verify redirect URI is exactly: http://localhost:8765/callback")

                            return None

                        code = params.get('code', [None])[0]
                        if code:
                            auth_code = code
                            _LOG.info(f"Extracted code from URL: {len(code)} characters")
                    # If it has code= but isn't a full URL, extract the value after code=
                    elif "code=" in auth_input:
                        parts = auth_input.split("code=")
                        if len(parts) > 1:
                            # Get everything after code= and before any & or other delimiters
                            code_part = parts[1].split("&")[0].split("#")[0]
                            auth_code = code_part
                            _LOG.info(f"Extracted code from query string: {len(auth_code)} characters")
                except Exception as e:
                    _LOG.warning(f"Failed to parse input, treating as plain code: {e}")

            _LOG.info(f"Authorization code length: {len(auth_code)}")

            # Exchange code for tokens
            await self.auth_mgr.request_tokens(auth_code)
            _LOG.info("OAuth2 tokens successfully retrieved from manual code.")

            return self.auth_mgr.oauth.model_dump()

        except Exception as e:
            _LOG.exception(f"Error during manual token exchange: {e}")
            return None

