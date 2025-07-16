import logging
import aiohttp
import ssl
import certifi
from ucapi import (
    DriverSetupRequest,
    UserDataResponse,
    AbortDriverSetup,
    SetupComplete,
    SetupError,
    IntegrationSetupError,
    RequestUserInput
)
from .config import XboxConfig
from .media_player import XboxMediaPlayer
from .auth import XboxAuth

_LOG = logging.getLogger("XBOX_SETUP")

class XboxSetup:
    def __init__(self, api, config: XboxConfig):
        self.api = api
        self.config = config
        self.auth_session = None

    async def handle_command(self, request):
        _LOG.info(f"👉 SETUP HANDLER CALLED! Request type: {type(request)}")
        
        # This is the correct pattern for the setup flow
        if isinstance(request, DriverSetupRequest):
            self.config.liveid = request.setup_data.get("liveid").strip()
            _LOG.info(f"...Live ID captured: {self.config.liveid}")

            ssl_context = ssl.create_default_context(cafile=certifi.where())
            self.auth_session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context))
            auth_handler = XboxAuth(self.auth_session)
            auth_url = await auth_handler.generate_auth_url()
            
            return RequestUserInput(
                {"en": "Xbox Authentication"},
                [
                    {"id": "info", "label": {"en": "Please log in to your Microsoft Account in a browser."}, "field": {"label": {"value": {"en": "A new window should have opened. If not, copy this URL."}}}},
                    {"id": "auth_url", "label": {"en": "Login URL"}, "field": {"text": {"value": auth_url, "read_only": True}}},
                    {"id": "redirect_url", "label": {"en": "Paste the full redirect URL here"}, "field": {"text": {"value": ""}}}
                ]
            )

        if isinstance(request, UserDataResponse):
            redirect_url = request.input_values.get("redirect_url")
            _LOG.info("...Received redirect URL from user.")

            auth_handler = XboxAuth(self.auth_session)
            tokens = await auth_handler.process_redirect_url(redirect_url)
            await self.auth_session.close() # Close the session now that we're done with it

            if not tokens:
                return SetupError(IntegrationSetupError.AUTHORIZATION_ERROR)
            
            self.config.tokens = tokens
            await self.config.save(self.api)
            _LOG.info("✅ Tokens successfully retrieved and saved.")

            await self.create_xbox_entity()
            return SetupComplete()

        if isinstance(request, AbortDriverSetup):
            _LOG.warning("...Setup was aborted.")
            if self.auth_session:
                await self.auth_session.close()
            return

        return SetupError(IntegrationSetupError.OTHER)

    async def create_xbox_entity(self):
        _LOG.info("Creating Xbox media player entity...")
        media_player = XboxMediaPlayer(self.api, self.config.liveid, None)
        # THIS IS THE FIX for the 'add_entity' error
        self.api.available_entities.add(media_player)
        _LOG.info(f"✅ Successfully added Xbox entity: {media_player.name}")