import logging
# We need to import the official SetupAction classes
from ucapi import DriverSetupRequest, AbortDriverSetup, SetupComplete, SetupError, IntegrationSetupError
from .config import XboxConfig
from .media_player import XboxMediaPlayer

_LOG = logging.getLogger("XBOX_SETUP")

class XboxSetup:
    def __init__(self, api, config: XboxConfig):
        self.api = api
        self.config = config
        _LOG.info("✅ SETUP HANDLER INITIALIZED (READY FOR DATA) ✅")

    async def handle_command(self, request):
        _LOG.info(f"👉 SETUP HANDLER CALLED! Request type: {type(request)}")

        if isinstance(request, DriverSetupRequest):
            live_id = request.setup_data.get("liveid")
            _LOG.info(f"...Data received from remote form: {request.setup_data}")

            if not live_id:
                _LOG.warning("...Live ID was not found in the setup data.")
                # Return an official SetupError object
                return SetupError(IntegrationSetupError.OTHER)

            self.config.liveid = live_id.strip()
            await self.config.save(self.api)
            _LOG.info(f"...Successfully saved Xbox Live ID: {self.config.liveid}")

            await self.create_xbox_entity()
            
            _LOG.info("...Setup is complete! Returning official SetupComplete object.")
            # CORRECTED: Return the official SetupComplete object
            return SetupComplete()
        
        if isinstance(request, AbortDriverSetup):
            _LOG.warning("...Setup was aborted by the user or remote.")
            # We don't need to return anything for an abort.
            return

        _LOG.warning(f"Unhandled setup request received: {request}")
        return SetupError(IntegrationSetupError.OTHER)

    async def create_xbox_entity(self):
        _LOG.info("Creating Xbox media player entity...")
        media_player = XboxMediaPlayer(self.api, self.config.liveid, None)
        self.api.available_entities.add(media_player)
        _LOG.info(f"Successfully added Xbox entity: {media_player.name}")