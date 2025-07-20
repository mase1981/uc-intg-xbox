import logging
import httpx
import ssl
import certifi
from enum import Enum

from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.authentication.models import OAuth2TokenResponse

_LOG = logging.getLogger("XBOX_DEVICE")

OAUTH2_DESKTOP_REDIRECT_URI = "https://login.live.com/oauth20_desktop.srf"

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

class XboxDevice:
    def __init__(self, client: XboxLiveClient, live_id: str):
        self.client = client
        self.live_id = live_id

    @classmethod
    async def from_config(cls, config, session: httpx.AsyncClient):
        _LOG.info("Authenticating Xbox client...")
        try:
            auth_mgr = AuthenticationManager(
                session, "388ea51c-0b25-4029-aae2-17df4f49d23905", None, OAUTH2_DESKTOP_REDIRECT_URI
            )
            auth_mgr.oauth = OAuth2TokenResponse.model_validate(config.tokens)
            await auth_mgr.refresh_tokens()
            client = XboxLiveClient(auth_mgr)
            return cls(client, config.liveid), auth_mgr.oauth.model_dump()
        except Exception as e:
            _LOG.exception("❌ Failed to authenticate Xbox client", exc_info=e)
            return None, None

    async def turn_on(self):
        """Uses the correct wake_up method from the latest library."""
        _LOG.info(f"🟢 Sending power on (wake_up) to Xbox Live ID: {self.live_id}")
        try:
            await self.client.smartglass.wake_up(self.live_id)
            _LOG.info("✅ Power on (wake_up) command sent successfully.")
        except Exception as e:
            _LOG.exception(f"❌ Failed to send power on command", exc_info=e)

    async def turn_off(self):
        """Uses the correct turn_off method from the latest library."""
        _LOG.info(f"🟢 Sending power off to Xbox Live ID: {self.live_id}")
        try:
            await self.client.smartglass.turn_off(self.live_id)
            _LOG.info("✅ Power off command sent.")
        except Exception as e:
            _LOG.exception(f"❌ Failed to send power off command", exc_info=e)

    async def press_button(self, button: str):
        _LOG.info(f"🔘 Sending button press: '{button}' to {self.live_id}")
        try:
            button_to_press = None
            if hasattr(SystemInput, button.capitalize()):
                button_to_press = SystemInput[button.capitalize()]
            elif hasattr(ControllerButtons, button):
                button_to_press = ControllerButtons[button]
            
            if button_to_press:
                await self.client.smartglass.press_button(self.live_id, button_to_press)
                _LOG.info(f"✅ Button '{button}' pressed.")
            else:
                _LOG.error(f"Unknown button command: {button}")
        except Exception as e:
            _LOG.exception(f"❌ Failed to press button '{button}'", exc_info=e)