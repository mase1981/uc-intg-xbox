import logging
from ucapi import MediaPlayer, StatusCodes
from ucapi import media_player
from .xbox import XboxDevice

_LOG = logging.getLogger("XBOX_ENTITY")

features = [
    media_player.Features.ON_OFF
]

class XboxMediaPlayer(MediaPlayer):
    """Definitive representation of an Xbox MediaPlayer, based on the JVC pattern."""

    def __init__(self, api, live_id: str, xbox_client):
        _LOG.info("✅ Initializing definitive JVC-style XboxMediaPlayer...")

        # Initialize with ONLY official attributes and NO 'api=' argument.
        super().__init__(
            identifier=f"xbox-{live_id}",
            name=f"Xbox ({live_id})",
            features=features,
            attributes={
                media_player.Attributes.STATE: media_player.States.OFF,
                media_player.Attributes.MEDIA_TYPE: media_player.MediaType.VIDEO,
            },
            # We link to our new, JVC-style command handler
            cmd_handler=self.media_player_cmd_handler
        )
        
        # Add custom attributes and store the api object AFTER initialization.
        self.attributes["manufacturer"] = "Microsoft"
        self.attributes["model"] = "Xbox"
        self.api = api
        self.unique_id = f"xbox-{live_id}"

        self.live_id = live_id
        self.device = None 
        _LOG.info(f"✅ XboxMediaPlayer entity fully initialized with ID: {self.unique_id}")

    async def media_player_cmd_handler(self, entity, cmd_id: str, params: dict = None) -> StatusCodes:
        """
        Handles commands sent from the remote, based on the JVC integration pattern.
        """
        _LOG.info(f"Command '{cmd_id}' received for entity '{self.unique_id}'.")
        
        # Compare the incoming command string to the Enum's .value
        if cmd_id == media_player.Commands.TurnOn.value:
            self.attributes[media_player.Attributes.STATE] = media_player.States.ON
            _LOG.info(f"POWER ON command received for {self.unique_id}")
            return StatusCodes.OK
        
        if cmd_id == media_player.Commands.TurnOff.value:
            self.attributes[media_player.Attributes.STATE] = media_player.States.OFF
            _LOG.info(f"POWER OFF command received for {self.unique_id}")
            return StatusCodes.OK
            
        return StatusCodes.NOT_IMPLEMENTED