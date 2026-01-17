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
from pythonxbox.scripts import CLIENT_ID, CLIENT_SECRET

_LOG = logging.getLogger("XBOX_AUTH")

# OAuth redirect URI - Out-of-band (OOB) flow
# This tells Microsoft to display the authorization code directly on the page
# instead of redirecting. This works without any external server or redirect URI!
OAUTH2_OOB_URI = "urn:ietf:wg:oauth:2.0:oob"

class XboxAuth:
    def __init__(self, session: httpx.AsyncClient):
        self.session = session
        self.auth_mgr = AuthenticationManager(
            session, CLIENT_ID, CLIENT_SECRET, OAUTH2_OOB_URI
        )
        _LOG.info("XboxAuth initialized with out-of-band flow.")

    def generate_auth_url(self) -> str:
        """Generate OAuth authorization URL that redirects to our callback page."""
        auth_url = self.auth_mgr.generate_authorization_url()
        _LOG.info(f"Generated auth URL: {auth_url[:100]}...")
        return auth_url

    async def process_auth_code(self, auth_code: str) -> dict | None:
        """
        Exchange authorization code for OAuth tokens.

        Args:
            auth_code: The authorization code copied from the callback page

        Returns:
            dict with OAuth tokens if successful, None otherwise
        """
        _LOG.info("Processing authorization code...")
        try:
            if not auth_code or not auth_code.strip():
                _LOG.error("Empty authorization code provided.")
                return None

            auth_code = auth_code.strip()
            _LOG.info(f"Authorization code length: {len(auth_code)}")

            await self.auth_mgr.request_tokens(auth_code)
            _LOG.info("✅ OAuth2 tokens successfully retrieved.")
            return self.auth_mgr.oauth.model_dump()
        except Exception as e:
            _LOG.exception(f"Error during token exchange: {e}")
            return None

