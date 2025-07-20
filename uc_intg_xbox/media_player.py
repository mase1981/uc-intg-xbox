import logging
import asyncio
import ucapi
import httpx
import ssl
import certifi
import re
from ucapi.media_player import Attributes, States
from ucapi import Remote, StatusCodes 

from .xbox_device import XboxDevice
from .config import XboxConfig

_LOG = logging.getLogger("XBOX_ENTITY")

# Add all desired buttons to the UI list
SUPPORTED_COMMANDS = [
    "on", "off", "up", "down", "left", "right", "select", "back", "home", "menu", "view",
    "a_button", "b_button", "x_button", "y_button",
    "play", "pause", "stop", "next_track", "previous_track",
    "red", "green", "blue", "yellow"
]

# Complete map from UI button ID to Xbox command
REMOTE_COMMANDS_MAP = {
    "on": "on", "off": "off", 
    "up": "DpadUp", "down": "DpadDown", "left": "DpadLeft", "right": "DpadRight", 
    "select": "A", "back": "B", "home": "Home", "menu": "Menu", "view": "View", 
    "a_button": "A", "b_button": "B", "x_button": "X", "y_button": "Y",
    "play": "Play", "pause": "Pause", "stop": "Stop", 
    "next_track": "NextTrack", "previous_track": "PrevTrack",
    "green": "A", "red": "B", "blue": "X", "yellow": "Y"
}

class XboxRemote(Remote):
    def __init__(self, api, config: XboxConfig, entity_id: str = ''):
        if not entity_id:
            entity_id = f"xbox-{config.liveid}"
        entity_name = {"en": f"Xbox ({config.liveid})"}
        super().__init__(
            entity_id, entity_name, [ucapi.remote.Features.ON_OFF],
            {Attributes.STATE: States.UNAVAILABLE},
            simple_commands=SUPPORTED_COMMANDS,
            cmd_handler=self.handle_command
        )
        self.api = api
        self.config = config
        self.device = None
        self.device_session = None
        asyncio.create_task(self._init_device())

    async def _init_device(self):
        _LOG.info("🔧 Initializing XboxDevice in background...")
        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            
            async def fix_microsoft_timestamps(response):
                if "user.auth.xboxlive.com" in str(response.url):
                    await response.aread()
                    response_text = response.text
                    fixed_text = re.sub(r"(\.\d{6})\d+Z", r"\1Z", response_text)
                    response._content = fixed_text.encode('utf-8')

            self.device_session = httpx.AsyncClient(
                verify=ssl_context, 
                event_hooks={'response': [fix_microsoft_timestamps]}
            )
            self.device, refreshed_tokens = await XboxDevice.from_config(self.config, self.device_session)
            if self.device:
                initial_state = {Attributes.STATE: States.OFF}
                self.api.configured_entities.update_attributes(self.id, initial_state)
                self.attributes.update(initial_state)
                self.config.tokens = refreshed_tokens
                await self.config.save(self.api)
                _LOG.info("✅ XboxDevice initialized and available.")
        except Exception:
            _LOG.exception("❌ Exception during XboxDevice initialization")

    async def handle_command(self, entity, cmd_id: str, params: dict = None) -> StatusCodes:
        if not self.device:
            return StatusCodes.ERROR
        try:
            actual_command = params.get("command") if cmd_id == ucapi.remote.Commands.SEND_CMD else cmd_id
            
            if actual_command == "on" or actual_command == ucapi.remote.Commands.ON:
                await self.device.turn_on()
                new_state = {Attributes.STATE: States.ON}
                self.api.configured_entities.update_attributes(self.id, new_state)
                self.attributes.update(new_state)
                return StatusCodes.OK
            elif actual_command == "off" or actual_command == ucapi.remote.Commands.OFF:
                await self.device.turn_off()
                new_state = {Attributes.STATE: States.OFF}
                self.api.configured_entities.update_attributes(self.id, new_state)
                self.attributes.update(new_state)
                return StatusCodes.OK
            elif actual_command in REMOTE_COMMANDS_MAP:
                button_to_press = REMOTE_COMMANDS_MAP[actual_command]
                await self.device.press_button(button_to_press)
                return StatusCodes.OK
            return StatusCodes.BAD_REQUEST
        except Exception as e:
            _LOG.exception(f"❌ Failed to execute command '{cmd_id}'", e)
            return StatusCodes.ERROR