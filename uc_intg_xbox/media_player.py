import logging
import asyncio
from ucapi.entity import Entity, EntityTypes
from ucapi.media_player import Features, Attributes, Commands, MediaType, States
from .xbox import XboxDevice
from .config import XboxConfig

_LOG = logging.getLogger("XBOX_ENTITY")

class XboxMediaPlayer(Entity):
    """MediaPlayer entity for Xbox, safely integrated with UC API and token-based control."""

    def __init__(self, api, config: XboxConfig, entity_id: str = ''):
        if not entity_id:
            entity_id = f"xbox-{config.liveid}"
        entity_name = {"en": f"Xbox ({config.liveid})"}

        super().__init__(
            identifier=entity_id,
            name=entity_name,
            entity_type=EntityTypes.MEDIA_PLAYER,
            features=[Features.ON_OFF.value],
            attributes={
                Attributes.STATE.value: States.UNAVAILABLE.value,
                Attributes.MEDIA_TYPE.value: MediaType.VIDEO.value,
                "manufacturer": "Microsoft",
                "model": "Xbox Series X"
            },
            cmd_handler=self.handle_command,
            #device_id=None
        )

        self.api = api
        self.config = config
        self.unique_id = entity_id
        self.device = None

        asyncio.create_task(self._init_device())

    async def _init_device(self):
        """Initializes the XboxDevice using current config tokens."""
        _LOG.info("🔧 Initializing XboxDevice in background...")
        try:
            self.device, refreshed_tokens = await XboxDevice.from_config(self.config)
            if self.device:
                self.attributes[Attributes.STATE.value] = States.OFF.value
                self.config.tokens = refreshed_tokens
                await self.config.save(self.api)
                _LOG.info("✅ XboxDevice initialized and tokens refreshed.")
            else:
                _LOG.warning("⚠️ XboxDevice creation returned None.")
        except Exception as e:
            _LOG.exception("❌ Exception during XboxDevice initialization:", exc_info=e)

    async def handle_command(self, entity, cmd_id: str, params: dict = None) -> bool:
        """Handles On/Off commands sent by UC Remote."""
        _LOG.info(f"📥 Command received: '{cmd_id}' for entity '{self.id}'.")

        if not self.device:
            _LOG.warning("⚠️ Device uninitialized. Attempting recovery...")
            try:
                self.device, refreshed_tokens = await XboxDevice.from_config(self.config)
                if self.device:
                    self.config.tokens = refreshed_tokens
                    await self.config.save(self.api)
            except Exception as e:
                _LOG.error("❌ Failed to reinitialize XboxDevice.")
                self.attributes[Attributes.STATE.value] = States.UNAVAILABLE.value
                return False

        if not self.device:
            return False

        try:
            if cmd_id == Commands.ON.value:
                await self.device.turn_on()
                self.attributes[Attributes.STATE.value] = States.ON.value
                return True

            elif cmd_id == Commands.OFF.value:
                await self.device.turn_off()
                self.attributes[Attributes.STATE.value] = States.OFF.value
                return True

            _LOG.warning(f"⚠️ Unsupported command: {cmd_id}")
            return False
        except Exception as e:
            _LOG.exception(f"❌ Failed to execute command '{cmd_id}'", exc_info=e)
            return False
