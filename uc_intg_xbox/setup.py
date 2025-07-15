import logging
from ucapi import DriverSetupRequest, AbortDriverSetup
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
                return {"type": "error", "message": "Live ID is required."}

            self.config.liveid = live_id.strip()
            await self.config.save(self.api)
            _LOG.info(f"...Successfully saved Xbox Live ID: {self.config.liveid}")

            await self.create_xbox_entity()
            
            _LOG.info("...Setup is complete! Telling the remote we are done.")
            return {"type": "finish_setup"}
        
        if isinstance(request, AbortDriverSetup):
            _LOG.warning("...Setup was aborted by the user or remote.")
            return

        _LOG.warning(f"Unhandled setup request received: {request}")
        return {"type": "error", "message": "An unexpected error occurred."}

    async def create_xbox_entity(self):
        """Creates and registers the Xbox entity."""
        _LOG.info("Creating Xbox media player entity...")
        media_player = XboxMediaPlayer(self.api, self.config.liveid, None)
        
        # CORRECTED: The method for ucapi v0.3.1 is self.api.available_entities.add()
        self.api.available_entities.add(media_player)
        
        _LOG.info(f"Successfully added Xbox entity: {media_player.name}")