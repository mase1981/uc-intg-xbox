import logging
import asyncio
import ucapi
import httpx
import ssl
import certifi
import re
from ucapi.media_player import Attributes, States, Commands, Features
from ucapi import Remote, StatusCodes
from ucapi.remote import States as RemoteStates

from xbox_device import XboxDevice
from config import XboxConfig

_LOG = logging.getLogger("XBOX_ENTITY")

SUPPORTED_COMMANDS = [
    "on",
    "off",
    "up",
    "down",
    "left",
    "right",
    "select",
    "back",
    "home",
    "menu",
    "view",
    "a_button",
    "b_button",
    "x_button",
    "y_button",
    "play",
    "pause",
    "stop",
    "next_track",
    "previous_track",
    "red",
    "green",
    "blue",
    "yellow",
    "volume_up",
    "volume_down",
    "mute_toggle",
]

REMOTE_COMMANDS_MAP = {
    "on": "on",
    "off": "off",
    "up": "Up",
    "down": "Down",
    "left": "Left",
    "right": "Right",
    "select": "A",
    "back": "B",
    "home": "Home",
    "menu": "Menu",
    "view": "View",
    "a_button": "A",
    "b_button": "B",
    "x_button": "X",
    "y_button": "Y",
    "play": "Play",
    "pause": "Pause",
    "stop": "Stop",
    "next_track": "NextTrack",
    "previous_track": "PrevTrack",
    "green": "A",
    "red": "B",
    "blue": "X",
    "yellow": "Y",
}


class XboxRemote(Remote):
    def __init__(self, api, config: XboxConfig, entity_id: str = ""):
        if not entity_id:
            entity_id = f"xbox-{config.liveid}"
        entity_name = {"en": f"Xbox ({config.liveid})"}
        super().__init__(
            entity_id,
            entity_name,
            features=[Features.ON_OFF, Features.VOLUME, Features.MUTE],
            attributes={"state": RemoteStates.ON},
            simple_commands=SUPPORTED_COMMANDS,
            cmd_handler=self.handle_command,
        )
        self.api = api
        self.config = config
        self.device = None
        self.device_session = None

    async def _init_device(self):
        """Initialize Xbox device with proactive token refresh like Xbox Live."""
        _LOG.info("🔧 Initializing XboxDevice in background...")
        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())

            async def fix_microsoft_timestamps(response):
                if "user.auth.xboxlive.com" in str(response.url):
                    await response.aread()
                    response_text = response.text
                    fixed_text = re.sub(r"(\.\d{6})\d+Z", r"\1Z", response_text)
                    response._content = fixed_text.encode("utf-8")

            self.device_session = httpx.AsyncClient(
                verify=ssl_context, event_hooks={"response": [fix_microsoft_timestamps]}
            )
            
            # Proactive token refresh on initialization (like Xbox Live)
            success = await self.refresh_authentication()
            
            if success:
                _LOG.info("✅ XboxDevice initialized and available.")
                self.api.configured_entities.update_attributes(self.id, {"state": RemoteStates.ON})
            else:
                _LOG.warning("⚠️ Xbox authentication failed - device unavailable")
                self.api.configured_entities.update_attributes(self.id, {"state": RemoteStates.OFF})
                
        except Exception as e:
            _LOG.exception("❌ Exception during XboxDevice initialization")
            self.api.configured_entities.update_attributes(self.id, {"state": RemoteStates.OFF})

    async def refresh_authentication(self):
        """Refresh Xbox authentication tokens (matching Xbox Live logic)."""
        try:
            if not self.config.tokens:
                _LOG.error("No tokens available for refresh")
                return False
                
            _LOG.info("🔄 Refreshing Xbox authentication tokens...")
            self.device, refreshed_tokens = await XboxDevice.from_config(
                self.config, self.device_session
            )
            
            if self.device and refreshed_tokens:
                # Save refreshed tokens immediately (like Xbox Live)
                self.config.tokens = refreshed_tokens
                await self.config.save(self.api)
                _LOG.info("✅ Xbox tokens refreshed successfully")
                return True
            else:
                _LOG.error("❌ Failed to refresh Xbox tokens")
                self.device = None
                return False
                
        except Exception as e:
            _LOG.exception("❌ Error refreshing Xbox authentication", exc_info=e)
            self.device = None
            return False

    async def handle_command(
        self, entity, cmd_id: str, params: dict = None
    ) -> StatusCodes:
        # Check if device is available
        if not self.device:
            _LOG.warning(f"❌ Xbox device not available - command '{cmd_id}' rejected. Attempting token refresh...")
            # Try to refresh authentication before failing
            if await self.refresh_authentication():
                _LOG.info("✅ Authentication refreshed, retrying command")
            else:
                _LOG.error("❌ Token refresh failed - device needs re-authentication.")
                return StatusCodes.BAD_REQUEST
        
        try:
            actual_command = (
                params.get("command")
                if cmd_id == ucapi.remote.Commands.SEND_CMD
                else cmd_id
            )

            if actual_command == "on" or actual_command == ucapi.remote.Commands.ON:
                await self.device.turn_on()
                self.api.configured_entities.update_attributes(self.id, {"state": RemoteStates.ON})
                return StatusCodes.OK
            elif actual_command == "off" or actual_command == ucapi.remote.Commands.OFF:
                await self.device.turn_off()
                self.api.configured_entities.update_attributes(self.id, {"state": RemoteStates.OFF})
                return StatusCodes.OK

            elif actual_command == Commands.VOLUME_UP:
                await self.device.change_volume("Up")
                return StatusCodes.OK
            elif actual_command == Commands.VOLUME_DOWN:
                await self.device.change_volume("Down")
                return StatusCodes.OK
            elif actual_command == Commands.MUTE_TOGGLE:
                await self.device.mute()
                return StatusCodes.OK

            elif actual_command in REMOTE_COMMANDS_MAP:
                button_to_press = REMOTE_COMMANDS_MAP[actual_command]
                await self.device.press_button(button_to_press)
                return StatusCodes.OK

            return StatusCodes.BAD_REQUEST
            
        except Exception as e:
            _LOG.exception(f"❌ Failed to execute command '{cmd_id}': {e}")
            # Check if it's an authentication error
            if "400 Bad Request" in str(e) or "oauth" in str(e).lower():
                _LOG.error("🔑 Xbox authentication has expired during command execution.")
                # Try to refresh authentication
                if await self.refresh_authentication():
                    _LOG.info("✅ Authentication refreshed after error")
                    self.api.configured_entities.update_attributes(self.id, {"state": RemoteStates.ON})
                else:
                    _LOG.error("❌ Token refresh failed - marking device unavailable")
                    self.device = None
                    self.api.configured_entities.update_attributes(self.id, {"state": RemoteStates.OFF})
            return StatusCodes.BAD_REQUEST