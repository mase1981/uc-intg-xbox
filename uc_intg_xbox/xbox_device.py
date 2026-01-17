import logging
import httpx
import ssl
import certifi
from enum import Enum

from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.authentication.models import OAuth2TokenResponse
from xbox.webapi.api.provider.smartglass.models import VolumeDirection
_LOG = logging.getLogger("XBOX_DEVICE")

OAUTH2_REDIRECT_URI = "http://localhost:8765/callback"

class SystemInput(str, Enum):
    A = "A"
    B = "B"
    Back = "Back"
    Home = "Home"
    Menu = "Menu"
    Nexus = "Nexus"
    View = "View"

class ControllerButtons(str, Enum):
    A = "A"
    B = "B"
    X = "X"
    Y = "Y"
    DpadUp = "Up"
    DpadDown = "Down"
    DpadLeft = "Left"
    DpadRight = "Right"
    Play = "Play"
    Pause = "Pause"
    Stop = "Stop"
    NextTrack = "NextTrack"
    PrevTrack = "PrevTrack"

class XboxDevice:
    def __init__(self, client: XboxLiveClient, live_id: str):
        self.client = client
        self.live_id = live_id

    @classmethod
    async def from_config(cls, config, session: httpx.AsyncClient):
        """Create Xbox device with proactive token refresh (matching Xbox Live logic)."""
        _LOG.info("Authenticating Xbox client...")
        try:
            # Use user-provided Azure App credentials from config
            auth_mgr = AuthenticationManager(
                session,
                config.client_id,
                config.client_secret,
                OAUTH2_REDIRECT_URI,
            )
            auth_mgr.oauth = OAuth2TokenResponse.model_validate(config.tokens)

            await auth_mgr.refresh_tokens()
            _LOG.info("✅ Successfully refreshed Xbox authentication tokens")
            
            client = XboxLiveClient(auth_mgr)
            
            return cls(client, config.liveid), auth_mgr.oauth.model_dump()
            
        except Exception as e:
            _LOG.exception("❌ Failed to authenticate Xbox client", exc_info=e)
            return None, None

    async def turn_on(self):
        _LOG.info(f"🟢 Sending power on (wake_up) to Xbox Live ID: {self.live_id}")
        try:
            await self.client.smartglass.wake_up(self.live_id)
            _LOG.info("✅ Power on (wake_up) command sent successfully.")
        except Exception as e:
            _LOG.exception(f"❌ Failed to send power on command", exc_info=e)
            raise

    async def turn_off(self):
        _LOG.info(f"🟢 Sending power off to Xbox Live ID: {self.live_id}")
        try:
            await self.client.smartglass.turn_off(self.live_id)
            _LOG.info("✅ Power off command sent.")
        except Exception as e:
            _LOG.exception(f"❌ Failed to send power off command", exc_info=e)
            raise

    async def change_volume(self, direction: str):
        _LOG.info(f"🔊 Sending Volume {direction} to {self.live_id}")
        try:
            direction_enum = VolumeDirection(direction)
            await self.client.smartglass.change_volume(self.live_id, direction_enum)
            _LOG.info(f"✅ Volume {direction} command sent successfully.")
        except Exception as e:
            _LOG.exception(f"❌ Failed to change volume", exc_info=e)
            raise

    async def mute(self):
        _LOG.info(f"🔇 Sending Mute to {self.live_id}")
        try:
            await self.client.smartglass.mute(self.live_id)
            _LOG.info("✅ Mute command sent successfully.")
        except Exception as e:
            _LOG.exception(f"❌ Failed to mute", exc_info=e)
            raise

    async def press_button(self, button: str):
        _LOG.info(f"🔘 Sending button press: '{button}' to {self.live_id}")
        try:
            button_to_press = None
            system_map = {e.value: e for e in SystemInput}
            controller_map = {e.value: e for e in ControllerButtons}

            if button in system_map:
                button_to_press = system_map[button]
            elif button in controller_map:
                button_to_press = controller_map[button]

            if button_to_press:
                await self.client.smartglass.press_button(self.live_id, button_to_press)
                _LOG.info(f"✅ Button '{button}' pressed successfully.")
            else:
                _LOG.error(f"Unknown button command: {button}")
                raise ValueError(f"Unknown button command: {button}")
        except Exception as e:
            _LOG.exception(f"❌ Failed to press button '{button}'", exc_info=e)
            raise