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
        _LOG.info(f"👉 Setup handler invoked with request type: {type(request)}")

        if isinstance(request, DriverSetupRequest):
            return await self._handle_driver_setup(request)

        elif isinstance(request, UserDataResponse):
            return await self._handle_user_data_response(request)

        elif isinstance(request, AbortDriverSetup):
            _LOG.warning("⚠️ Setup aborted by user.")
            await self._cleanup_session()
            return

        _LOG.error(f"🔥 Unhandled setup request type: {type(request)}")
        return SetupError(IntegrationSetupError.OTHER)

    async def _handle_driver_setup(self, request):
        self.config.liveid = request.setup_data.get("liveid", "").strip()
        _LOG.info(f"📥 Captured Live ID: {self.config.liveid}")

        if not self.config.liveid:
            _LOG.error("❌ Live ID is missing or empty.")
            return SetupError(IntegrationSetupError.OTHER)

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.auth_session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=ssl_context)
        )

        auth_handler = XboxAuth(self.auth_session)
        auth_url = auth_handler.generate_auth_url()

        return RequestUserInput(
            {"en": "Xbox Authentication"},
            [
                {
                    "id": "info",
                    "label": {"en": "Please log in to your Microsoft Account in a browser."},
                    "field": {
                        "label": {
                            "value": {"en": "A new window should have opened. If not, copy this URL."}
                        }
                    },
                },
                {
                    "id": "auth_url",
                    "label": {"en": "Login URL"},
                    "field": {"text": {"value": auth_url, "read_only": True}},
                },
                {
                    "id": "redirect_url",
                    "label": {"en": "Paste the full redirect URL here"},
                    "field": {"text": {"value": ""}},
                },
            ]
        )

    async def _handle_user_data_response(self, request):
        redirect_url = request.input_values.get("redirect_url", "").strip()
        _LOG.info("📥 Received redirect URL from user.")

        if not redirect_url:
            _LOG.error("❌ Redirect URL is empty or invalid.")
            await self._cleanup_session()
            return SetupError(IntegrationSetupError.AUTHORIZATION_ERROR)

        auth_handler = XboxAuth(self.auth_session)
        try:
            tokens = await auth_handler.process_redirect_url(redirect_url)
        finally:
            await self._cleanup_session()

        if not tokens:
            _LOG.error("❌ Failed to retrieve valid tokens from redirect.")
            return SetupError(IntegrationSetupError.AUTHORIZATION_ERROR)

        self.config.tokens = tokens
        await self.config.save(self.api)
        _LOG.info("✅ Tokens saved to configuration.")

        try:
            await self.create_xbox_entity()
            _LOG.info("✅ Xbox entity created successfully.")
            return SetupComplete()
        except Exception as e:
            _LOG.exception(f"❌ Failed during Xbox entity creation: {e}")
            return SetupError(IntegrationSetupError.OTHER)

    async def create_xbox_entity(self):
        _LOG.info("🔧 Creating XboxMediaPlayer entity...")
        media_player = XboxMediaPlayer(self.api, self.config)
        self.api.available_entities.add(media_player)
        _LOG.info(f"✅ XboxMediaPlayer '{media_player.name}' registered.")

    async def _cleanup_session(self):
        if self.auth_session and not self.auth_session.closed:
            _LOG.info("🔒 Closing aiohttp auth session.")
            await self.auth_session.close()
