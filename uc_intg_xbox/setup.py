import logging
from ucapi import (
    DriverSetupRequest,
    AbortDriverSetup,
    SetupComplete,
    SetupError,
    IntegrationSetupError,
    DeviceStates  # ✅ Added for connection state handling
)
from .config import XboxConfig
from .media_player import XboxMediaPlayer

_LOG = logging.getLogger("XBOX_SETUP")

class XboxSetup:
    def __init__(self, api, config: XboxConfig):
        self.api = api
        self.config = config
        _LOG.info("✅ SETUP HANDLER INITIALIZED ✅")

    async def handle_command(self, request):
        _LOG.info(f"👉 SETUP HANDLER CALLED! Request type: {type(request)}")

        if isinstance(request, DriverSetupRequest):
            live_id = request.setup_data.get("liveid")
            _LOG.info(f"...Data received from remote form: {live_id}")

            if not live_id:
                _LOG.warning("...Live ID was not found.")
                return SetupError(IntegrationSetupError.OTHER)

            self.config.liveid = live_id.strip()
            await self.config.save(self.api)
            _LOG.info(f"...Saved Xbox Live ID: {self.config.liveid}")

            await self.create_xbox_entity()

            _LOG.info("...Setup is complete. Returning official SetupComplete object.")
            return SetupComplete()

        if isinstance(request, AbortDriverSetup):
            _LOG.warning("...Setup was aborted by the user or remote.")
            return

        _LOG.warning(f"Unhandled setup request: {request}")
        return SetupError(IntegrationSetupError.OTHER)

    async def create_xbox_entity(self):
        _LOG.info("Creating Xbox media player entity...")
        media_player = XboxMediaPlayer(self.api, self.config.liveid, None)
        self.api.available_entities.add(media_player)
        _LOG.info(f"✅ Successfully added Xbox entity: {media_player.name}")

        # ✅ Notify Remote that the integration is online
        await self.api.set_device_state(DeviceStates.CONNECTED)
        _LOG.info("✅ Driver state set to CONNECTED.")
