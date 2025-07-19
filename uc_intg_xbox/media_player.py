import logging
import asyncio
import ucapi
from ucapi.media_player import Attributes, States
from ucapi import Remote, StatusCodes 

from .xbox_device import XboxDevice
from .config import XboxConfig

_LOG = logging.getLogger("XBOX_ENTITY")

# The list of commands we want the remote to show buttons for.
# 'on' is not included as we decided to focus on a working 'off'.
SUPPORTED_COMMANDS = [
    "off", "up", "down", "left", "right", "select", 
    "back", "home", "menu", "info"
]

# This maps the commands from the remote to the commands the xbox-webapi needs.
REMOTE_COMMANDS_MAP = {
    "up": "dpad_up", "down": "dpad_down", "left": "dpad_left", "right": "dpad_right",
    "select": "a", "back": "b", "home": "nexus", "menu": "menu", "info": "view",
}

class XboxRemote(Remote):
    def __init__(self, api, config: XboxConfig, entity_id: str = ''):
        if not entity_id:
            entity_id = f"xbox-{config.liveid}"
        entity_name = {"en": f"Xbox ({config.liveid})"}

        super().__init__(
            entity_id,
            entity_name,
            [ucapi.remote.Features.ON_OFF],
            {Attributes.STATE: States.UNAVAILABLE},
            simple_commands=SUPPORTED_COMMANDS,
            cmd_handler=self.handle_command
        )
        self.api = api
        self.config = config
        self.device = None
        asyncio.create_task(self._init_device())

    async def _init_device(self):
        _LOG.info("🔧 Initializing XboxDevice...")
        try:
            self.device, refreshed_tokens = await XboxDevice.from_config(self.config)
            if self.device:
                initial_state = {Attributes.STATE: States.OFF}
                self.api.configured_entities.update_attributes(self.id, initial_state)
                self.attributes.update(initial_state)
                self.config.tokens = refreshed_tokens
                await self.config.save(self.api)
                _LOG.info("✅ XboxDevice initialized.")
        except Exception as e:
            _LOG.exception("❌ Exception during XboxDevice initialization:", e)

    async def handle_command(self, entity, cmd_id: str, params: dict = None) -> StatusCodes:
        _LOG.info(f"📥 Command received: '{cmd_id}' with params: {params}")
        if not self.device:
            await self._init_device()
            if not self.device: return StatusCodes.ERROR

        try:
            actual_command = None
            # Check for the generic 'send_cmd' from our simple_commands list
            if cmd_id == ucapi.remote.Commands.SEND_CMD:
                actual_command = params.get("command")
            # The main on/off buttons might send a direct command
            elif cmd_id == ucapi.remote.Commands.OFF:
                actual_command = "off"

            if not actual_command:
                _LOG.warning(f"⚠️ Could not determine actual command from cmd_id: {cmd_id}")
                return StatusCodes.BAD_REQUEST

            # Now, process the actual command
            if actual_command == "off":
                await self.device.turn_off()
                new_state = {Attributes.STATE: States.OFF}
                self.api.configured_entities.update_attributes(self.id, new_state)
                self.attributes.update(new_state)
                return StatusCodes.OK
            elif actual_command in REMOTE_COMMANDS_MAP:
                button_to_press = REMOTE_COMMANDS_MAP[actual_command]
                await self.device.press_button(button_to_press)
                return StatusCodes.OK
            
            _LOG.warning(f"⚠️ Unsupported actual command: {actual_command}")
            return StatusCodes.BAD_REQUEST
        except Exception as e:
            _LOG.exception(f"❌ Failed to execute command '{cmd_id}'", e)
            return StatusCodes.ERROR