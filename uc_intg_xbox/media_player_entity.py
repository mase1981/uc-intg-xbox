"""
Xbox media player entity module for Unfolded Circle integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from ucapi.media_player import MediaPlayer, Attributes, Features, States, Commands

_LOG = logging.getLogger("XBOX_MEDIA_PLAYER")

class XboxMediaPlayer(MediaPlayer):
    def __init__(self, api, xbox_client, entity_id: str = ""):
        if not entity_id:
            entity_id = f"xbox-player-{xbox_client.live_id}"
        entity_name = {"en": f"Xbox ({xbox_client.gamertag})"}
        
        super().__init__(
            entity_id,
            entity_name,
            features=[
                Features.ON_OFF,
                Features.TOGGLE,
                Features.VOLUME,
                Features.VOLUME_UP_DOWN,
                Features.MUTE_TOGGLE,
                Features.MUTE,
                Features.UNMUTE,
                Features.PLAY_PAUSE,
                Features.STOP,
                Features.NEXT,
                Features.PREVIOUS,
                Features.MEDIA_TITLE,
                Features.MEDIA_IMAGE_URL,
                Features.MEDIA_TYPE,
                Features.DPAD,
                Features.HOME,
                Features.MENU,
                Features.CONTEXT_MENU,
            ],
            attributes={
                Attributes.STATE: States.OFF,
                Attributes.MEDIA_TITLE: "Offline",
                Attributes.MEDIA_IMAGE_URL: "",
                Attributes.MEDIA_TYPE: "GAME",
            },
            cmd_handler=self.handle_command,
        )
        self.api = api
        self.xbox_client = xbox_client
        _LOG.info(f"XboxMediaPlayer entity initialized for {entity_name}")

    async def handle_command(self, entity, cmd_id: str, params: dict = None):
        if not self.xbox_client or not self.xbox_client.client:
            _LOG.warning(f"Xbox client not available - command '{cmd_id}' rejected")
            return
        
        try:
            if cmd_id == Commands.ON:
                await self.xbox_client.turn_on()
                
            elif cmd_id == Commands.OFF:
                await self.xbox_client.turn_off()
                
            elif cmd_id == Commands.TOGGLE:
                current_state = self.attributes.get(Attributes.STATE)
                if current_state == States.ON or current_state == States.PLAYING:
                    await self.xbox_client.turn_off()
                else:
                    await self.xbox_client.turn_on()
                    
            elif cmd_id == Commands.PLAY_PAUSE:
                current_state = self.attributes.get(Attributes.STATE)
                if current_state == States.PLAYING:
                    await self.xbox_client.press_button("Pause")
                else:
                    await self.xbox_client.press_button("Play")
                    
            elif cmd_id == Commands.STOP:
                await self.xbox_client.press_button("Stop")
                
            elif cmd_id == Commands.NEXT:
                await self.xbox_client.press_button("NextTrack")
                
            elif cmd_id == Commands.PREVIOUS:
                await self.xbox_client.press_button("PrevTrack")
                
            elif cmd_id == Commands.VOLUME_UP:
                await self.xbox_client.change_volume("Up")
                
            elif cmd_id == Commands.VOLUME_DOWN:
                await self.xbox_client.change_volume("Down")
                
            elif cmd_id == Commands.MUTE_TOGGLE:
                await self.xbox_client.mute()
                
            elif cmd_id == Commands.MUTE:
                await self.xbox_client.mute()
                
            elif cmd_id == Commands.UNMUTE:
                await self.xbox_client.unmute()
                
            elif cmd_id == Commands.CURSOR_UP:
                await self.xbox_client.press_button("Up")
                
            elif cmd_id == Commands.CURSOR_DOWN:
                await self.xbox_client.press_button("Down")
                
            elif cmd_id == Commands.CURSOR_LEFT:
                await self.xbox_client.press_button("Left")
                
            elif cmd_id == Commands.CURSOR_RIGHT:
                await self.xbox_client.press_button("Right")
                
            elif cmd_id == Commands.CURSOR_ENTER:
                await self.xbox_client.press_button("A")
                
            elif cmd_id == Commands.BACK:
                await self.xbox_client.press_button("B")
                
            elif cmd_id == Commands.HOME:
                await self.xbox_client.press_button("Home")
                
            elif cmd_id == Commands.MENU:
                await self.xbox_client.press_button("Menu")
                
            elif cmd_id == Commands.CONTEXT_MENU:
                await self.xbox_client.press_button("View")
                
            elif cmd_id == Commands.FUNCTION_RED:
                await self.xbox_client.press_button("B")
                
            elif cmd_id == Commands.FUNCTION_GREEN:
                await self.xbox_client.press_button("A")
                
            elif cmd_id == Commands.FUNCTION_BLUE:
                await self.xbox_client.press_button("X")
                
            elif cmd_id == Commands.FUNCTION_YELLOW:
                await self.xbox_client.press_button("Y")
                
        except Exception as e:
            _LOG.exception(f"Failed to execute command '{cmd_id}': {e}")

    async def update_presence(self, presence_data: dict):
        attributes_to_update = {}
        
        new_state = presence_data.get("state")
        if self.attributes.get(Attributes.STATE) != new_state:
            attributes_to_update[Attributes.STATE] = new_state
        
        new_title = presence_data.get("title", "Unknown")
        if self.attributes.get(Attributes.MEDIA_TITLE) != new_title:
            attributes_to_update[Attributes.MEDIA_TITLE] = new_title

        new_image = presence_data.get("image", "")
        if self.attributes.get(Attributes.MEDIA_IMAGE_URL) != new_image:
            attributes_to_update[Attributes.MEDIA_IMAGE_URL] = new_image

        if attributes_to_update:
            self.api.configured_entities.update_attributes(self.id, attributes_to_update)
            _LOG.info(f"Media player updated: {attributes_to_update}")