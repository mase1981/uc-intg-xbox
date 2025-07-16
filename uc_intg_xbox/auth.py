import logging
from urllib.parse import urlparse, parse_qs
import aiohttp
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.scripts import CLIENT_ID, CLIENT_SECRET

_LOG = logging.getLogger("XBOX_AUTH")

class XboxAuth:
    def __init__(self, session: aiohttp.ClientSession):
        self.auth_mgr = AuthenticationManager(session, CLIENT_ID, CLIENT_SECRET, "")

    async def generate_auth_url(self) -> str:
        return self.auth_mgr.generate_authorization_url()

    async def process_redirect_url(self, redirect_url: str) -> dict:
        try:
            parsed_url = urlparse(redirect_url)
            query_params = parse_qs(parsed_url.query)
            auth_code = query_params.get("code", [None])[0]
            if not auth_code:
                return None
            await self.auth_mgr.request_tokens(auth_code)
            return self.auth_mgr.oauth.dict()
        except Exception as e:
            _LOG.error(f"Failed to process redirect URL: {e}")
            return None