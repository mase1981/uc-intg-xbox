import logging
import aiohttp
import ssl
import certifi
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.scripts import CLIENT_ID, CLIENT_SECRET

_LOG = logging.getLogger("XBOX_AUTH")

class XboxAuth:
    """Handles the Xbox Live authentication flow."""

    def __init__(self):
        self.auth_mgr = None

    async def generate_auth_url(self) -> str:
        """Generates the Microsoft login URL for the user."""
        _LOG.info("Generating Xbox Live auth URL...")
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            self.auth_mgr = AuthenticationManager(
                session, CLIENT_ID, CLIENT_SECRET, ""
            )
            auth_url = self.auth_mgr.generate_authorization_url()
            _LOG.info(f"Auth URL generated: {auth_url}")
            return auth_url

    async def process_redirect_url(self, redirect_url: str) -> dict:
        """Processes the redirect URL to get tokens."""
        _LOG.info("Processing redirect URL to get tokens...")
        from urllib.parse import urlparse, parse_qs

        try:
            parsed_url = urlparse(redirect_url)
            query_params = parse_qs(parsed_url.query)
            auth_code = query_params.get("code", [None])[0]

            if not auth_code:
                _LOG.error("Could not find authorization code in the redirect URL.")
                return None

            await self.auth_mgr.request_tokens(auth_code)
            tokens = self.auth_mgr.oauth.dict()
            _LOG.info("Successfully retrieved tokens.")
            return tokens

        except Exception as e:
            _LOG.error(f"Failed to process redirect URL: {e}")
            return None