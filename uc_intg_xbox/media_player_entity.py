"""
Xbox media player entity module for Unfolded Circle integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from ucapi.media_player import MediaPlayer

_LOG = logging.getLogger("XBOX_MEDIA_PLAYER")

async def empty_command_handler(entity, command, params=None):
    _LOG.info(f"Command '{command}' received. No action taken (read-only entity).")
    return True

class XboxMediaPlayer(MediaPlayer):
    def __init__(self, api, xbox_client, entity_id: str = ""):
        if not entity_id:
            entity_id = f"xbox-player-{xbox_client.live_id}"
        entity_name = {"en": f"Xbox ({xbox_client.gamertag})"}
        
        super().__init__(
            entity_id,
            entity_name,
            features=["ON_OFF", "MEDIA_TITLE", "MEDIA_IMAGE_URL", "MEDIA_TYPE"],
            attributes={
                "state": "OFF",
                "media_title": "Offline",
                "media_image_url": "",
                "media_type": "GAME",
            },
            cmd_handler=empty_command_handler,
        )
        self.api = api
        self.xbox_client = xbox_client
        _LOG.info(f"XboxMediaPlayer entity initialized for {entity_name}")

    async def update_presence(self, presence_data: dict):
        attributes_to_update = {}
        
        new_state = presence_data.get("state")
        if self.attributes.get("state") != new_state:
            attributes_to_update["state"] = new_state
        
        new_title = presence_data.get("title", "Unknown")
        if self.attributes.get("media_title") != new_title:
            attributes_to_update["media_title"] = new_title

        new_image = presence_data.get("image", "")
        if self.attributes.get("media_image_url") != new_image:
            attributes_to_update["media_image_url"] = new_image

        if attributes_to_update:
            self.api.configured_entities.update_attributes(self.id, attributes_to_update)
            _LOG.info(f"Media player updated: {attributes_to_update}")