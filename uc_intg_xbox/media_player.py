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
        _LOG.info("✅ Initializing definitive JVC-style XboxMediaPlayer...")

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
        
        # Step 2: Add custom attributes and store the api object AFTER initialization.
        self.attributes["manufacturer"] = "Microsoft"
        self.attributes["model"] = "Xbox"
        self.api = api
        self.unique_id = f"xbox-{live_id}"

        self.live_id = live_id
        self.device = None 
        _LOG.info(f"✅ XboxMediaPlayer entity fully initialized with ID: {self.unique_id}")

    async def handle_command(self, command: media_player.Commands, value: any = None) -> bool:
        """Handles commands sent from the remote."""
        _LOG.info(f"Command '{command.name}' received for entity '{self.unique_id}'.")
        
        if command == media_player.Commands.TurnOn:
            self.attributes[media_player.Attributes.STATE] = media_player.States.ON
            _LOG.info(f"POWER ON command received for {self.unique_id}")
            return True
        
        if command == media_player.Commands.TurnOff:
            self.attributes[media_player.Attributes.STATE] = media_player.States.OFF
            _LOG.info(f"POWER OFF command received for {self.unique_id}")
            return True
            
        return False