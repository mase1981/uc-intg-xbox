import logging
import asyncio  # ✅ Required for background task creation
from ucapi.entity import Entity, EntityTypes
from ucapi.media_player import Features, Attributes, Commands, MediaType, States
from .xbox import XboxDevice
from .config import XboxConfig

_LOG = logging.getLogger("XBOX_ENTITY")

class XboxMediaPlayer(Entity):
    """
    Definitive representation of an Xbox entity, combining the best of our code.
    """
    def __init__(self, api, config: XboxConfig):
        super().__init__(
            identifier=f"xbox-{config.liveid}",
            name=f"Xbox ({config.liveid})",
            entity_type=EntityTypes.MEDIA_PLAYER,
            features=[
                Features.ON_OFF.value
            ],
            attributes={
                Attributes.STATE.value: States.UNAVAILABLE.value,
                Attributes.MEDIA_TYPE.value: MediaType.VIDEO.value,
                "manufacturer": "Microsoft",
                "model": "Xbox Series X"
            },
            cmd_handler=self.handle_command
        )

        self.api = api
        self.config = config
        self.unique_id = f"xbox-{config.liveid}"
        self.device = None

        # ✅ Fixed: use asyncio directly for background task creation
        asyncio.create_task(self._init_device())

    async def _init_device(self):
        """Initializes XboxDevice in the background."""
        _LOG.info("🔧 Initializing XboxDevice in background...")
        try:
            self.device, refreshed_tokens = await XboxDevice.from_config(self.config)
            if self.device:
                self.attributes[Attributes.STATE.value] = States.OFF.value
                self.config.tokens = refreshed_tokens
                await self.config.save(self.api)
                _LOG.info("✅ XboxDevice created successfully and state set to OFF.")
            else:
                _LOG.warning("⚠️ XboxDevice creation failed during init.")
        except Exception as e:
            _LOG.exception("❌ Exception during XboxDevice init:", exc_info=e)

    async def handle_command(self, entity, cmd_id: str, params: dict = None) -> bool:
        """Handles TurnOn and TurnOff commands."""
        _LOG.info(f"📥 Command received: '{cmd_id}' for entity '{self.id}'.")

        if not self.device:
            _LOG.warning("Device was uninitialized. Attempting to recover.")
            self.device, refreshed_tokens = await XboxDevice.from_config(self.config)
            if self.device:
                self.config.tokens = refreshed_tokens
                await self.config.save(self.api)

        if not self.device:
            _LOG.error("❌ Failed to create Xbox device. Command failed.")
            self.attributes[Attributes.STATE.value] = States.UNAVAILABLE.value
            return False

        try:
            if cmd_id == Commands.TurnOn.value:
                await self.device.turn_on()
                self.attributes[Attributes.STATE.value] = States.ON.value
                return True

            if cmd_id == Commands.TurnOff.value:
                await self.device.turn_off()
                self.attributes[Attributes.STATE.value] = States.OFF.value
                return True

            _LOG.warning(f"⚠️ Unsupported command: {cmd_id}")
            return False
        except Exception as e:
            _LOG.exception(f"❌ Failed to execute command '{cmd_id}'", exc_info=e)
            return False
