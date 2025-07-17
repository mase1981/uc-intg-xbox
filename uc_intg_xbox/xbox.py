import logging
from xbox.webapi.api.client import XboxLiveClient
from xbox.sg.console import Console
import aiohttp
import ssl
import certifi

_LOG = logging.getLogger(__name__)

class XboxDevice:
    """Represents the Xbox console and handles all communication with it."""
    def __init__(self, client: XboxLiveClient, live_id: str):
        self.client = client
        self.live_id = live_id

    @classmethod
    async def from_config(cls, config):
        """Create an authenticated XboxDevice instance from a config object."""
        _LOG.info("Creating authenticated XboxLiveClient...")
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
            auth_mgr = AuthenticationManager(
                session, config.tokens["client_id"], 
                config.tokens["client_secret"], ""
            )
            auth_mgr.oauth = OAuth2TokenResponse.parse_obj(config.tokens)
            await auth_mgr.refresh_tokens()
            
            client = XboxLiveClient(auth_mgr)
            return cls(client, config.liveid)

    async def turn_on(self):
        _LOG.info(f"🟢 Sending power on to Xbox Live ID: {self.live_id}")
        try:
            await Console.power_on(liveid=self.live_id, tries=5)
            _LOG.info("✅ Power on command sent successfully.")
        except Exception as e:
            _LOG.exception(f"❌ Failed to send power on command: {e}")

    async def turn_off(self):
        _LOG.warning("⚠️ Power off is not supported via this simple method.")
        # The new API requires a more complex REST call for shutdown.
        # This can be implemented as a future enhancement.
        pass