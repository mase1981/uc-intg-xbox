import logging
import asyncio
import socket
import aiohttp
import ssl
import certifi

from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.authentication.models import OAuth2TokenResponse
from xbox.webapi.scripts import CLIENT_ID, CLIENT_SECRET

_LOG = logging.getLogger("XBOX_DEVICE")

OAUTH2_DESKTOP_REDIRECT_URI = "https://login.live.com/oauth20_desktop.srf"

class XboxDevice:
    """Represents the Xbox console and handles all communication with it."""
    def __init__(self, client: XboxLiveClient, live_id: str):
        self.client = client
        self.live_id = live_id

    @classmethod
    async def from_config(cls, config):
        """Creates a live XboxDevice instance from a config object."""
        _LOG.info("Creating XboxDevice from config...")
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
            try:
                auth_mgr = AuthenticationManager(
                    session, CLIENT_ID, CLIENT_SECRET, OAUTH2_DESKTOP_REDIRECT_URI
                )
                auth_mgr.oauth = OAuth2TokenResponse.parse_obj(config.tokens)
                await auth_mgr.refresh_tokens()

                client = XboxLiveClient(auth_mgr)
                _LOG.info("✅ XboxLiveClient created and authenticated.")
                return cls(client, config.liveid), auth_mgr.oauth.dict()
            except Exception as e:
                _LOG.exception("❌ Failed to authenticate Xbox client:", exc_info=e)
                return None, None

    async def turn_on(self):
        """Send Wake-on-LAN packet to Xbox Live ID."""
        _LOG.info(f"🟢 Sending power-on broadcast to Xbox Live ID: {self.live_id}")
        try:
            packet = b'\xdd\x02\x00\x0e\x00\x00' + self.live_id.encode()
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                for _ in range(5):
                    sock.sendto(packet, ("255.255.255.255", 5050))
                    await asyncio.sleep(0.5)
            _LOG.info("✅ Power-on broadcast sent.")
        except Exception as e:
            _LOG.exception("❌ Failed to send power-on packet", exc_info=e)

    async def turn_off(self):
        """Use the authenticated client to send the power off command."""
        _LOG.info(f"🟢 Sending power off to Xbox Live ID: {self.live_id}")
        try:
            await self.client.power_off(self.live_id)
            _LOG.info("✅ Power off command sent successfully.")
        except Exception as e:
            _LOG.exception(f"❌ Failed to send power off command: {e}")
