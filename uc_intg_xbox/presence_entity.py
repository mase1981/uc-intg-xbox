import logging
from ucapi.media_player import MediaPlayer

_LOG = logging.getLogger("XBOX_PRESENCE_ENTITY")

async def empty_command_handler(command, value):
    _LOG.info(f"Command received and ignored: {command}")
    return True

class XboxPresenceMediaPlayer(MediaPlayer):
    def __init__(self, api, live_id: str, gamertag: str):
        self.api = api
        super().__init__(
            identifier=f"xbox-presence-{live_id}",
            name=gamertag,
            features=[],
            attributes={
                "state": "UNAVAILABLE",
                "title": "Offline",
                "artist": "Xbox Live",
                "album_art_uri": None,
                "media_type": "GAME"
            },
            cmd_handler=empty_command_handler
        )
        _LOG.info(f"✅ XboxPresenceMediaPlayer entity '{gamertag}' initialized.")

    def update_presence(self, presence_data: dict):
        new_title = presence_data.get("title", "Home")
        new_art_uri = presence_data.get("image")
        new_state = "PLAYING" if presence_data.get("state", "").lower() == "online" else "OFF"

        attributes_to_update = {}

        if self.attributes.get("title") != new_title:
            attributes_to_update["title"] = new_title
        if self.attributes.get("album_art_uri") != new_art_uri:
            attributes_to_update["album_art_uri"] = new_art_uri
        if self.attributes.get("state") != new_state:
            attributes_to_update["state"] = new_state

        if attributes_to_update:
            self.attributes.update(attributes_to_update)
            self.api.configured_entities.update_attributes(self.id, attributes_to_update)
            _LOG.info(f"Entity updated: {attributes_to_update}")