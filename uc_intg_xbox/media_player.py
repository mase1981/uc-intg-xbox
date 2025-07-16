import logging
from ucapi import MediaPlayer
from ucapi import media_player
from .xbox import XboxDevice

_LOG = logging.getLogger("XBOX_ENTITY")

features = [
    media_player.Features.ON_OFF
]

class XboxMediaPlayer(MediaPlayer):
    def __init__(self, api, live_id: str, xbox_client):
        super().__init__(
            identifier=f"xbox-{live_id}",
            name=f"Xbox ({live_id})",
            features=features,
            attributes={
                media_player.Attributes.STATE: media_player.States.OFF,
                media_player.Attributes.MEDIA_TYPE: media_player.MediaType.VIDEO,
            },
            cmd_handler=self.handle_command
        )
        
        self.attributes["manufacturer"] = "Microsoft"
        self.attributes["model"] = "Xbox"
        self.api = api
        self.unique_id = f"xbox-{live_id}"
        self.live_id = live_id
        self.device = None 
        _LOG.info(f"✅ XboxMediaPlayer entity initialized with ID: {self.unique_id}")

    async def handle_command(self, command: media_player.Commands, value: any = None) -> bool:
        _LOG.info(f"Command '{command.name}' received for entity '{self.unique_id}'.")
        return True