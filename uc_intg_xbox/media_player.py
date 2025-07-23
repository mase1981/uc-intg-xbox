import logging
import asyncio
import ucapi
import httpx
import ssl
import certifi
import re
from ucapi.media_player import Attributes, States, Commands, Features
from ucapi import Remote, StatusCodes

from xbox_device import XboxDevice
from config import XboxConfig

_LOG = logging.getLogger("XBOX_ENTITY")

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
    def __init__(self, api, config: XboxConfig, entity_id: str = ""):
        if not entity_id:
            entity_id = f"xbox-{config.liveid}"
        entity_name = {"en": f"Xbox ({config.liveid})"}

        # --- CORRECTED SECTION ---
        super().__init__(
            entity_id,
            entity_name,
            features=[Features.ON_OFF, Features.VOLUME, Features.MUTE],
            attributes={
                Attributes.STATE: States.UNAVAILABLE,
                "title": "Offline",
                "artist": "Xbox",
                "album_art_uri": None,
                "media_type": "GAME"
            },
            simple_commands=SUPPORTED_COMMANDS,
            cmd_handler=self.handle_command
        )
        # -------------------------

        self.api = api
        self.config = config
        self.device = None
        self.device_session = None
        asyncio.create_task(self._init_device())

    def update_presence(self, presence_data: dict):
        """Updates the entity attributes based on new presence data."""
        new_title = presence_data.get("title", "Home")
        new_art_uri = presence_data.get("image")
        new_state = "PLAYING" if presence_data.get("state", "").lower() == "online" else "OFF"

        attributes_to_update = {}

        if self.attributes.get("title") != new_title:
            attributes_to_update["title"] = new_title
        if self.attributes.get("album_art_uri") != new_art_uri:
            attributes_to_update["album_art_uri"] = new_art_uri

        if new_state == "OFF":
            if self.attributes.get("state") != new_state:
                attributes_to_update["state"] = new_state

        if attributes_to_update:
            self.attributes.update(attributes_to_update)
            self.api.configured_entities.update_attributes(self.id, attributes_to_update)
            _LOG.info(f"Presence updated: {attributes_to_update}")

    async def _init_device(self):
        # ... (rest of the file is unchanged)
