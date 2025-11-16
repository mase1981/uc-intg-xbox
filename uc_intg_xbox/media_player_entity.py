"""
Xbox media player entity module for Unfolded Circle integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from ucapi.media_player import MediaPlayer, Attributes, Features, States

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
        _LOG.info(f"XboxMediaPlayer entity '{entity_name}' initialized.")

    async def handle_command(self, entity, cmd_id: str, params: dict = None):
        if not self.xbox_client or not self.xbox_client.client:
            _LOG.warning(f"Xbox client not available - command '{cmd_id}' rejected")
            return
        
        try:
            if cmd_id == "media_player.on":
                await self.xbox_client.turn_on()
                
            elif cmd_id == "media_player.off":
                await self.xbox_client.turn_off()
                
            elif cmd_id == "media_player.toggle":
                current_state = self.attributes.get(Attributes.STATE)
                if current_state == States.ON or current_state == States.PLAYING:
                    await self.xbox_client.turn_off()
                else:
                    await self.xbox_client.turn_on()
                    
            elif cmd_id == "media_player.play_pause":
                current_state = self.attributes.get(Attributes.STATE)
                if current_state == States.PLAYING:
                    await self.xbox_client.press_button("Pause")
                else:
                    await self.xbox_client.press_button("Play")
                    
            elif cmd_id == "media_player.stop":
                await self.xbox_client.press_button("Stop")
                
            elif cmd_id == "media_player.next":
                await self.xbox_client.press_button("NextTrack")
                
            elif cmd_id == "media_player.previous":
                await self.xbox_client.press_button("PrevTrack")
                
            elif cmd_id == "media_player.volume_up":
                await self.xbox_client.volume("Up")
                
            elif cmd_id == "media_player.volume_down":
                await self.xbox_client.volume("Down")
                
            elif cmd_id == "media_player.mute_toggle":
                await self.xbox_client.mute()
                
            elif cmd_id == "media_player.mute":
                await self.xbox_client.mute()
                
            elif cmd_id == "media_player.unmute":
                await self.xbox_client.unmute()
                
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