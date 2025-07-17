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
        _LOG.info(f"👉 Setup handler called with request type: {type(request)}")

        if isinstance(request, DriverSetupRequest):
            self.config.liveid = request.setup_data.get("liveid", "").strip()
            _LOG.info(f"📥 Captured Live ID: {self.config.liveid}")

            if not self.config.liveid:
                _LOG.error("❌ Live ID missing or invalid.")
                return SetupError(IntegrationSetupError.OTHER)

            # Init secure HTTPS session
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            self.auth_session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=ssl_context)
            )

            # Create auth URL
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

        elif isinstance(request, UserDataResponse):
            redirect_url = request.input_values.get("redirect_url", "").strip()
            _LOG.info("📥 Received redirect URL from user.")

            if not redirect_url:
                _LOG.error("❌ No redirect URL provided.")
                await self._cleanup_session()
                return SetupError(IntegrationSetupError.AUTHORIZATION_ERROR)

            auth_handler = XboxAuth(self.auth_session)
            try:
                tokens = await auth_handler.process_redirect_url(redirect_url)
            finally:
                await self._cleanup_session()

            if not tokens:
                _LOG.error("❌ Failed to retrieve tokens.")
                return SetupError(IntegrationSetupError.AUTHORIZATION_ERROR)

            self.config.tokens = tokens
            await self.config.save(self.api)
            _LOG.info("✅ Tokens saved to config.")

            try:
                await self.create_xbox_entity()
                _LOG.info("✅ Xbox entity created.")
                return SetupComplete()
            except Exception as e:
                _LOG.exception(f"❌ Failed during Xbox entity creation: {e}")
                return SetupError(IntegrationSetupError.OTHER)

        elif isinstance(request, AbortDriverSetup):
            _LOG.warning("⚠️ Setup was aborted.")
            await self._cleanup_session()
            return

        _LOG.error(f"🔥 Unhandled setup request type: {type(request)}")
        return SetupError(IntegrationSetupError.OTHER)

    async def create_xbox_entity(self):
        _LOG.info("🔧 Creating XboxMediaPlayer entity...")
        media_player = XboxMediaPlayer(self.api, self.config.liveid, None)
        self.api.available_entities.add(media_player)
        _LOG.info(f"✅ XboxMediaPlayer '{getattr(media_player, 'name', 'Unnamed')}' registered.")

    async def _cleanup_session(self):
        if self.auth_session and not self.auth_session.closed:
            _LOG.info("🔒 Closing auth session.")
            await self.auth_session.close()
