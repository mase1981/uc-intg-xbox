import logging
from urllib.parse import urlparse, parse_qs
import aiohttp
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.authentication.models import OAuth2TokenResponse
from xbox.webapi.scripts import CLIENT_ID, CLIENT_SECRET

_LOG = logging.getLogger("XBOX_AUTH")

OAUTH2_DESKTOP_REDIRECT_URI = "https://login.live.com/oauth20_desktop.srf"
OAUTH2_TOKEN_URL = "https://login.live.com/oauth20_token.srf"

class XboxAuth:
    """Handles the Xbox Live authentication flow with a persistent session."""

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        # We still use the auth_mgr to generate the initial URL
        self.auth_mgr = AuthenticationManager(
            session, CLIENT_ID, CLIENT_SECRET, OAUTH2_DESKTOP_REDIRECT_URI
        )
        _LOG.info("XboxAuth initialized.")

    def generate_auth_url(self) -> str:
        """Generates the Microsoft login URL for the user."""
        return self.auth_mgr.generate_authorization_url()

    async def process_redirect_url(self, redirect_url: str) -> dict | None:
        """
        Processes the redirect URL to get tokens by sending a manual POST request.
        """
        _LOG.info("Processing redirect URL via manual POST request...")
        try:
            parsed_url = urlparse(redirect_url)
            query_params = parse_qs(parsed_url.query)
            auth_code = query_params.get("code", [None])[0]

            if not auth_code:
                _LOG.error("Could not find authorization code in the redirect URL.")
                return None

            # THIS IS THE FIX: We build the request manually, just like your original script.
            token_request_body = {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": auth_code,
                "grant_type": "authorization_code",
                "redirect_uri": OAUTH2_DESKTOP_REDIRECT_URI,
                "scope": "Xboxlive.signin Xboxlive.offline_access",
            }

            async with self.session.post(OAUTH2_TOKEN_URL, data=token_request_body) as resp:
                resp.raise_for_status() # This will raise an error if the request fails
                tokens = await resp.json()
            
            # The library expects the token data in a specific object format, so we'll
            # parse it into the object and then convert it back to a dictionary for saving.
            self.auth_mgr.oauth = OAuth2TokenResponse.parse_obj(tokens)
            
            _LOG.info("✅ Successfully retrieved tokens via manual POST.")
            return self.auth_mgr.oauth.dict()

        except aiohttp.ClientResponseError as e:
            _LOG.error(f"Failed to get tokens. Status: {e.status}, Message: {e.message}")
            return None
        except Exception as e:
            _LOG.error(f"An unexpected error occurred during token exchange: {e}", exc_info=True)
            return None