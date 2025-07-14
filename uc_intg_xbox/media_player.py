import logging
from ucapi.media_player import MediaPlayer, Commands, Attributes, MediaType
from .xbox import XboxDevice

_LOG = logging.getLogger("XBOX_ENTITY")

class XboxMediaPlayer(MediaPlayer):
    def __init__(self, api, live_id: str, xbox_client):
        super().__init__(api)
        self.unique_id = f"xbox-{live_id}"
        self.name = f"Xbox ({live_id})"
        self.media_type = MediaType.GAME_CONSOLE
        self.attributes[Attributes.MANUFACTURER] = "Microsoft"
        self.attributes[Attributes.MODEL] = "Xbox"
        
        self.add_command(Commands.TurnOn)
        self.add_command(Commands.TurnOff)
        
        self.device = None # Add real device later

    async def handle_command(self, command: Commands, value: any = None) -> bool:
        _LOG.info(f"Command '{command.name}' received.")
        return True # Placeholder