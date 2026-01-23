"""
Xbox remote entity module for Unfolded Circle integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from ucapi import Remote, StatusCodes
from ucapi.remote import States as RemoteStates, Features, Commands

_LOG = logging.getLogger("XBOX_REMOTE")

SIMPLE_COMMANDS = [
    "POWER_ON",
    "POWER_OFF",
    "POWER_TOGGLE",
    "DPAD_UP",
    "DPAD_DOWN",
    "DPAD_LEFT",
    "DPAD_RIGHT",
    "DPAD_CENTER",
    "BACK",
    "HOME",
    "NEXUS",
    "MENU",
    "CONTEXT_MENU",
    "CHANNEL_UP",
    "CHANNEL_DOWN",
    "A",
    "B",
    "X",
    "Y",
    "PLAY",
    "PAUSE",
    "NEXT",
    "PREVIOUS",
    "FAST_FORWARD",
    "REWIND",
    "VOLUME_UP",
    "VOLUME_DOWN",
    "MUTE_TOGGLE",
    "RED",
    "GREEN",
    "BLUE",
    "YELLOW",
]

COMMAND_MAP = {
    "POWER_ON": "on",
    "POWER_OFF": "off",
    "POWER_TOGGLE": "toggle",
    "DPAD_UP": "Up",
    "DPAD_DOWN": "Down",
    "DPAD_LEFT": "Left",
    "DPAD_RIGHT": "Right",
    "DPAD_CENTER": "A",
    "BACK": "B",
    "HOME": "Guide",
    "NEXUS": "Nexus",
    "MENU": "Menu",
    "CONTEXT_MENU": "View",
    "CHANNEL_UP": "Y",
    "CHANNEL_DOWN": "X",
    "A": "A",
    "B": "B",
    "X": "X",
    "Y": "Y",
    "PLAY": "play",
    "PAUSE": "pause",
    "NEXT": "next",
    "PREVIOUS": "previous",
    "FAST_FORWARD": "next",
    "REWIND": "previous",
    "VOLUME_UP": "volume_up",
    "VOLUME_DOWN": "volume_down",
    "MUTE_TOGGLE": "mute",
    "RED": "B",
    "GREEN": "A",
    "BLUE": "X",
    "YELLOW": "Y",
}

class XboxRemote(Remote):
    def __init__(self, api, xbox_client, console_name: str = None, liveid: str = None):
        # Use provided console name or fallback to gamertag
        display_name = console_name or f"Xbox ({xbox_client.gamertag})"

        # Use liveid for entity ID to ensure uniqueness
        self.liveid = liveid or xbox_client.live_id
        entity_id = f"xbox-remote-{self.liveid}"
        entity_name = {"en": f"{display_name} Remote"}

        super().__init__(
            entity_id,
            entity_name,
            features=[Features.ON_OFF, Features.TOGGLE, Features.SEND_CMD],
            attributes={"state": RemoteStates.ON},
            simple_commands=SIMPLE_COMMANDS,
            cmd_handler=self.handle_command,
        )
        self.api = api
        self.xbox_client = xbox_client
        _LOG.info(f"XboxRemote entity initialized: {entity_id} - {entity_name}")

    async def handle_command(self, entity, cmd_id: str, params: dict = None) -> StatusCodes:
        if not self.xbox_client or not self.xbox_client.client:
            _LOG.warning(f"Xbox client not available - command '{cmd_id}' rejected")
            return StatusCodes.BAD_REQUEST
        
        try:
            from uc_intg_xbox.driver import trigger_state_update, trigger_delayed_state_update
            
            if cmd_id == Commands.ON:
                await self.xbox_client.turn_on()
                self.api.configured_entities.update_attributes(self.id, {"state": RemoteStates.ON})
                trigger_state_update(self.liveid)
                return StatusCodes.OK

            elif cmd_id == Commands.OFF:
                await self.xbox_client.turn_off()
                self.api.configured_entities.update_attributes(self.id, {"state": RemoteStates.OFF})
                trigger_state_update(self.liveid)
                return StatusCodes.OK
                
            elif cmd_id == Commands.TOGGLE:
                current_state = self.attributes.get("state")
                if current_state == RemoteStates.ON:
                    await self.xbox_client.turn_off()
                    self.api.configured_entities.update_attributes(self.id, {"state": RemoteStates.OFF})
                else:
                    await self.xbox_client.turn_on()
                    self.api.configured_entities.update_attributes(self.id, {"state": RemoteStates.ON})
                trigger_state_update(self.liveid)
                return StatusCodes.OK

            elif cmd_id == Commands.SEND_CMD and params:
                command = params.get("command")
                if command in COMMAND_MAP:
                    xbox_cmd = COMMAND_MAP[command]

                    if xbox_cmd == "on":
                        await self.xbox_client.turn_on()
                        trigger_state_update(self.liveid)
                    elif xbox_cmd == "off":
                        await self.xbox_client.turn_off()
                        trigger_state_update(self.liveid)
                    elif xbox_cmd == "volume_up":
                        await self.xbox_client.change_volume("Up")
                    elif xbox_cmd == "volume_down":
                        await self.xbox_client.change_volume("Down")
                    elif xbox_cmd == "mute":
                        await self.xbox_client.mute()
                    elif xbox_cmd == "play":
                        await self.xbox_client.play()
                    elif xbox_cmd == "pause":
                        await self.xbox_client.pause()
                    elif xbox_cmd in ["next", "fast_forward"]:
                        await self.xbox_client.next_track()
                    elif xbox_cmd in ["previous", "rewind"]:
                        await self.xbox_client.previous_track()
                    else:
                        await self.xbox_client.press_button(xbox_cmd)
                        if xbox_cmd in ["Guide", "Nexus", "A", "B"]:
                            trigger_state_update(self.liveid)
                            trigger_delayed_state_update(self.liveid)

                    return StatusCodes.OK

            return StatusCodes.BAD_REQUEST
            
        except Exception as e:
            _LOG.exception(f"Failed to execute command '{cmd_id}': {e}")
            return StatusCodes.BAD_REQUEST