import logging
import asyncio
import aiohttp
import ssl
import certifi
from enum import Enum

from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.authentication.models import OAuth2TokenResponse
from xbox.webapi.scripts import CLIENT_ID, CLIENT_SECRET

_LOG = logging.getLogger("XBOX_DEVICE")

OAUTH2_DESKTOP_REDIRECT_URI = "https://login.live.com/oauth20_desktop.srf"

class GamePad(str, Enum):
    A = "a"
    B = "b"
    X = "x"
    Y = "y"
    DPAD_UP = "dpad_up"
    DPAD_DOWN = "dpad_down"
    DPAD_LEFT = "dpad_left"
    DPAD_RIGHT = "dpad_right"
    VIEW = "view"
    MENU = "menu"
    NEXUS = "nexus"

class XboxDevice:
    def __init__(self, client: XboxLiveClient, live_id: str):
        self.client = client
        self.live_id = live_id

    @classmethod
    async def from_config(cls, config):
        _LOG.info("Authenticating Xbox client...")
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        # Create the session without 'async with' so it stays open
        session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context))

        try:
            auth_mgr = AuthenticationManager(
                session, CLIENT_ID, CLIENT_SECRET, OAUTH2_DESKTOP_REDIRECT_URI
            )
            auth_mgr.oauth = OAuth2TokenResponse.parse_obj(config.tokens)
            await auth_mgr.refresh_tokens()
            client = XboxLiveClient(auth_mgr)
            # The session is now held open by the client object
            return cls(client, config.liveid), auth_mgr.oauth.dict()
        except Exception as e:
            _LOG.exception("❌ Failed to authenticate Xbox client", exc_info=e)
            # If we fail, we must close the session we created
            await session.close()
            return None, None

    async def turn_off(self):
        """Turns the console off by sending a sequence of button presses."""
        _LOG.info(f"🟢 Sending power off sequence to Xbox Live ID: {self.live_id}")
        try:
            await self.client.smartglass.press_button(self.live_id, GamePad.NEXUS)
            await asyncio.sleep(2)
            await self.client.smartglass.press_button(self.live_id, GamePad.A)
            _LOG.info("✅ Power off sequence sent successfully.")
        except Exception as e:
            _LOG.exception(f"❌ Failed to send power off sequence", exc_info=e)

    async def press_button(self, button: str):
        """Uses the smartglass client to press a button."""
        _LOG.info(f"🔘 Sending button press: '{button}' to {self.live_id}")
        try:
            button_to_press = GamePad(button)
            await self.client.smartglass.press_button(self.live_id, button_to_press)
            _LOG.info(f"✅ Button '{button}' pressed.")
        except Exception as e:
            _LOG.exception(f"❌ Failed to press button '{button}'", exc_info=e)