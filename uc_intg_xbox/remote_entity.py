"""
Xbox remote entity module for Unfolded Circle integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from ucapi import Remote, StatusCodes
from ucapi.remote import States as RemoteStates
from ucapi.remote import Features

_LOG = logging.getLogger("XBOX_REMOTE")

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
    def __init__(self, api, xbox_client, entity_id: str = ""):
        if not entity_id:
            entity_id = f"xbox-remote-{xbox_client.live_id}"
        entity_name = {"en": f"Xbox Remote ({xbox_client.gamertag})"}
        
        super().__init__(
            entity_id,
            entity_name,
            features=[Features.ON_OFF, Features.VOLUME, Features.MUTE],
            attributes={"state": RemoteStates.ON},
            simple_commands=SUPPORTED_COMMANDS,
            cmd_handler=self.handle_command,
        )
        self.api = api
        self.xbox_client = xbox_client
        _LOG.info(f"XboxRemote entity '{entity_name}' initialized.")

    async def handle_command(self, entity, cmd_id: str, params: dict = None) -> StatusCodes:
        if not self.xbox_client or not self.xbox_client.client:
            _LOG.warning(f"Xbox client not available - command '{cmd_id}' rejected")
            return StatusCodes.BAD_REQUEST
        
        try:
            actual_command = (
                params.get("command")
                if cmd_id == "remote.send_cmd"
                else cmd_id
            )

            if actual_command == "on" or actual_command == "remote.on":
                await self.xbox_client.turn_on()
                self.api.configured_entities.update_attributes(self.id, {"state": RemoteStates.ON})
                return StatusCodes.OK
                
            elif actual_command == "off" or actual_command == "remote.off":
                await self.xbox_client.turn_off()
                self.api.configured_entities.update_attributes(self.id, {"state": RemoteStates.OFF})
                return StatusCodes.OK

            elif actual_command == "volume_up":
                await self.xbox_client.volume("Up")
                return StatusCodes.OK
                
            elif actual_command == "volume_down":
                await self.xbox_client.volume("Down")
                return StatusCodes.OK
                
            elif actual_command == "mute_toggle":
                await self.xbox_client.mute()
                return StatusCodes.OK

            elif actual_command in REMOTE_COMMANDS_MAP:
                button_to_press = REMOTE_COMMANDS_MAP[actual_command]
                await self.xbox_client.press_button(button_to_press)
                return StatusCodes.OK

            return StatusCodes.BAD_REQUEST
            
        except Exception as e:
            _LOG.exception(f"Failed to execute command '{cmd_id}': {e}")
            return StatusCodes.BAD_REQUEST