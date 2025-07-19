import logging
from urllib.parse import urlparse, parse_qs
import aiohttp
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.authentication.models import OAuth2TokenResponse
from xbox.webapi.scripts import CLIENT_ID, CLIENT_SECRET

_LOG = logging.getLogger("XBOX_AUTH")

OAUTH2_DESKTOP_REDIRECT_URI = "https://login.live.com/oauth20_desktop.srf"

class XboxAuth:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.auth_mgr = AuthenticationManager(
            session, CLIENT_ID, CLIENT_SECRET, OAUTH2_DESKTOP_REDIRECT_URI
        )
        _LOG.info("XboxAuth initialized.")

    def generate_auth_url(self) -> str:
        return self.auth_mgr.generate_authorization_url()

    async def process_redirect_url(self, redirect_url: str) -> dict | None:
        _LOG.info("Processing redirect URL...")
        try:
            parsed_url = urlparse(redirect_url)
            query_params = parse_qs(parsed_url.query)
            auth_code = query_params.get("code", [None])[0]

            if not auth_code:
                return None

            await self.auth_mgr.request_tokens(auth_code)
            _LOG.info("✅ OAuth2 tokens successfully retrieved.")
            return self.auth_mgr.oauth.dict()
        except Exception:
            _LOG.exception("Unexpected error during token exchange.")
            return None