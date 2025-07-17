import logging
from ucapi import MediaPlayer
from ucapi import media_player
from .xbox import XboxDevice
from .config import XboxConfig

_LOG = logging.getLogger("XBOX_ENTITY")

class XboxMediaPlayer(MediaPlayer):
    def __init__(self, api, config: XboxConfig, xbox_client):
        # We pass the whole config object now
        self.config = config
        super().__init__(
            identifier=f"xbox-{config.liveid}",
            name=f"Xbox ({config.liveid})",
            features=[media_player.Features.ON_OFF],
            attributes={
                media_player.Attributes.STATE: media_player.States.OFF,
                media_player.Attributes.MEDIA_TYPE: media_player.MediaType.VIDEO,
                "manufacturer": "Microsoft",
                "model": "Xbox"
            },
            cmd_handler=self.handle_command
        )
        self.api = api
        self.unique_id = f"xbox-{config.liveid}"
        self.device = None # We will create this on-demand

    async def handle_command(self, command: media_player.Commands, value: any = None) -> bool:
        _LOG.info(f"Command '{command.name}' received for entity '{self.unique_id}'.")
        
        try:
            _LOG.info("Attempting to create live Xbox device for command...")
            self.device = await XboxDevice.from_config(self.config)
            _LOG.info("Live Xbox device created successfully.")
        except Exception as e:
            _LOG.error(f"❌ Failed to create live Xbox device: {e}")
            self.attributes[media_player.Attributes.STATE] = media_player.States.UNAVAILABLE
            return False

        if command == media_player.Commands.TurnOn:
            await self.device.turn_on()
            self.attributes[media_player.Attributes.STATE] = media_player.States.ON
            return True
        
        if command == media_player.Commands.TurnOff:
            await self.device.turn_off()
            self.attributes[media_player.Attributes.STATE] = media_player.States.OFF
            return True
            
        return False