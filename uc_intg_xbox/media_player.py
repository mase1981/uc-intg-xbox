import logging
from ucapi.entity import Entity, EntityTypes
from ucapi.media_player import Features, Attributes, Commands, MediaType
from .xbox import XboxDevice

_LOG = logging.getLogger("XBOX_ENTITY")

class XboxMediaPlayer(Entity):
    """
    Represents an Xbox entity, built from the base Entity class for stability.
    This pattern is based on the working JVC integration and fixes the data formatting bug.
    """
    def __init__(self, api, live_id: str, xbox_client):
        # We manually define all properties of the base Entity class,
        # using .value to ensure all enums are converted to simple strings.
        super().__init__(
            identifier=f"xbox-{live_id}",
            name=f"Xbox ({live_id})",
            entity_type=EntityTypes.MEDIA_PLAYER.value,
            features=[
                Features.ON_OFF.value
            ],
            attributes={
                Attributes.STATE.value: "OFF",
                Attributes.MEDIA_TYPE.value: MediaType.VIDEO.value,
                "manufacturer": "Microsoft",
                "model": "Xbox"
            },
            cmd_handler=self.handle_command
        )
        
        self.api = api
        self.live_id = live_id
        self.device = None
        _LOG.info(f"✅ JVC-STYLE XboxMediaPlayer entity initialized with ID: {self.id}")

    async def handle_command(self, entity, cmd_id: str, params: dict = None) -> bool:
        """Handles commands sent from the remote."""
        _LOG.info(f"Command '{cmd_id}' received for entity '{self.id}'.")
        
        # In this older library, we return a simple boolean.
        if cmd_id == Commands.TurnOn.value:
            self.attributes[Attributes.STATE.value] = "ON"
            return True
        
        if cmd_id == Commands.TurnOff.value:
            self.attributes[Attributes.STATE.value] = "OFF"
            return True
            
        return False