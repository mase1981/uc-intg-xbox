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
        )
        self.api = api
        self.xbox_client = xbox_client
        _LOG.info(f"XboxMediaPlayer entity initialized for {entity_name}")

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