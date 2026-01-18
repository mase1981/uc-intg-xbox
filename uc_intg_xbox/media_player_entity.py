"""
Xbox media player entity module for Unfolded Circle integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from ucapi import StatusCodes
from ucapi.media_player import MediaPlayer, DeviceClasses

_LOG = logging.getLogger("XBOX_MEDIA_PLAYER")

class XboxMediaPlayer(MediaPlayer):
    def __init__(self, api, xbox_client, console_name: str = None, liveid: str = None):
        # Use provided console name or fallback to gamertag
        display_name = console_name or f"Xbox ({xbox_client.gamertag})"

        # Use liveid for entity ID to ensure uniqueness
        entity_id = f"xbox-player-{liveid or xbox_client.live_id}"
        entity_name = {"en": display_name}

        super().__init__(
            entity_id,
            entity_name,
            features=[],
            attributes={
                "state": "OFF",
                "media_title": "Offline",
                "media_image_url": "",
                "media_type": "GAME",
            },
            device_class=DeviceClasses.RECEIVER,
            cmd_handler=self.handle_command,
        )
        self.api = api
        self.xbox_client = xbox_client
        _LOG.info(f"XboxMediaPlayer entity initialized: {entity_id} - {entity_name}")

    async def handle_command(self, entity, cmd_id: str, params: dict | None = None) -> StatusCodes:
        _LOG.debug(f"Command '{cmd_id}' received. Ignoring (read-only entity).")
        return StatusCodes.OK

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