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

_LOG = logging.getLogger("XBOX_AUTH")

# OAuth redirect URI - Localhost redirect
# User's custom Azure App must have http://localhost properly registered
# This allows the OAuth flow to work correctly with personal Microsoft/Xbox accounts
OAUTH2_LOCALHOST_URI = "http://localhost"

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
            session, client_id, client_secret, OAUTH2_LOCALHOST_URI
        )
        _LOG.info("XboxAuth initialized with user-provided credentials and localhost redirect.")

    def generate_auth_url(self) -> str:
        """Generate OAuth authorization URL that redirects to our callback page."""
        auth_url = self.auth_mgr.generate_authorization_url()
        _LOG.info(f"Generated auth URL: {auth_url[:100]}...")
        return auth_url

    async def process_auth_code(self, auth_input: str) -> dict | None:
        """
        Exchange authorization code for OAuth tokens.

        Args:
            auth_input: Either the full redirect URL or just the authorization code

        Returns:
            dict with OAuth tokens if successful, None otherwise
        """
        _LOG.info("Processing authorization input...")
        try:
            if not auth_input or not auth_input.strip():
                _LOG.error("Empty authorization input provided.")
                return None

            auth_input = auth_input.strip()

            # Try to extract code from URL if user pasted full URL
            auth_code = auth_input
            if auth_input.startswith("http://localhost") or auth_input.startswith("http%3A%2F%2Flocalhost"):
                _LOG.info("Detected full redirect URL, extracting code...")
                try:
                    from urllib.parse import urlparse, parse_qs, unquote
                    # Handle URL-encoded URLs
                    if auth_input.startswith("http%3A"):
                        auth_input = unquote(auth_input)

                    parsed = urlparse(auth_input)
                    params = parse_qs(parsed.query)
                    code = params.get('code', [None])[0]
                    if code:
                        auth_code = code
                        _LOG.info(f"Extracted code from URL: {len(code)} characters")
                except Exception as e:
                    _LOG.warning(f"Failed to parse URL, treating as plain code: {e}")

            _LOG.info(f"Authorization code length: {len(auth_code)}")

            await self.auth_mgr.request_tokens(auth_code)
            _LOG.info("✅ OAuth2 tokens successfully retrieved.")
            return self.auth_mgr.oauth.model_dump()
        except Exception as e:
            _LOG.exception(f"Error during token exchange: {e}")
            return None

