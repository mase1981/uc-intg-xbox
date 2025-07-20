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

class SystemInput(str, Enum):
    Nexus = "Nexus"
    View = "View"
    Menu = "Menu"
    A = "A"
    B = "B"

class ControllerButtons(str, Enum):
    Up = "Up"
    Down = "Down"
    Left = "Left"
    Right = "Right"
    A = "A"
    B = "B"
    X = "X"
    Y = "Y"
    # Add Media Buttons here
    Play = "Play"
    Pause = "Pause"
    Stop = "Stop"
    NextTrack = "NextTrack"
    PreviousTrack = "PreviousTrack"

class XboxDevice:
    def __init__(self, client: XboxLiveClient, live_id: str):
        self.client = client
        self.live_id = live_id

    @classmethod
    async def from_config(cls, config):
        session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl.create_default_context(cafile=certifi.where())))
        try:
            auth_mgr = AuthenticationManager(
                session, CLIENT_ID, CLIENT_SECRET, OAUTH2_DESKTOP_REDIRECT_URI
            )
            auth_mgr.oauth = OAuth2TokenResponse.parse_obj(config.tokens)
            await auth_mgr.refresh_tokens()
            client = XboxLiveClient(auth_mgr)
            return cls(client, config.liveid), auth_mgr.oauth.dict()
        except Exception as e:
            await session.close()
            _LOG.exception("❌ Failed to authenticate Xbox client", exc_info=e)
            return None, None

    async def turn_off(self):
        _LOG.info(f"🟢 Sending power off sequence to Xbox Live ID: {self.live_id}")
        try:
            await self.client.smartglass.press_button(self.live_id, SystemInput.Nexus)
            await asyncio.sleep(2)
            await self.client.smartglass.press_button(self.live_id, SystemInput.A)
            _LOG.info("✅ Power off sequence sent.")
        except Exception as e:
            _LOG.exception(f"❌ Failed to send power off sequence", exc_info=e)

    async def press_button(self, button: str):
        _LOG.info(f"🔘 Sending button press: '{button}' to {self.live_id}")
        try:
            button_to_press = None
            if button in SystemInput._value2member_map_:
                button_to_press = SystemInput(button)
            elif button in ControllerButtons._value2member_map_:
                button_to_press = ControllerButtons(button)
            
            if button_to_press:
                await self.client.smartglass.press_button(self.live_id, button_to_press)
                _LOG.info(f"✅ Button '{button}' pressed successfully.")
            else:
                _LOG.error(f"Unknown button command: {button}")
        except Exception as e:
            _LOG.exception(f"❌ Failed to press button '{button}'", exc_info=e)