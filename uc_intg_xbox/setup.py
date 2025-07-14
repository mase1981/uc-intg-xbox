import logging
# We need to import the specific message types we're handling
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

        # Check if the remote sent the form data
        if isinstance(request, DriverSetupRequest):
            # The older library uses setup_data, not input_values
            live_id = request.setup_data.get("liveid")

            if not live_id:
                _LOG.warning("...Live ID was not found in the setup data.")
                return {"type": "error", "message": "Live ID is required."}

            self.config.liveid = live_id.strip()
            await self.config.save(self.api)
            _LOG.info(f"...Successfully saved Xbox Live ID: {self.config.liveid}")

            await self.create_xbox_entity()
            
            _LOG.info("...Setup is complete! Telling the remote we are done.")
            return {"type": "finish_setup"}
        
        # Check if the user cancelled the setup
        if isinstance(request, AbortDriverSetup):
            _LOG.warning("...Setup was aborted by the user or remote.")
            # We don't need to do anything, just acknowledge
            return

        # If we get here, something unexpected happened.
        _LOG.error(f"Unhandled setup request received: {request}")
        return {"type": "error", "message": "An unexpected error occurred."}


    async def create_xbox_entity(self):
        _LOG.info("Creating Xbox media player entity...")
        media_player = XboxMediaPlayer(self.api, self.config.liveid, None)
        self.api.add_entity(media_player)
        _LOG.info(f"Successfully added Xbox entity: {media_player.name}")