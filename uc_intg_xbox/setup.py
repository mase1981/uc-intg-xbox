import logging
import aiohttp
import ssl
import certifi
from ucapi import (
    DriverSetupRequest, UserDataResponse, AbortDriverSetup,
    SetupComplete, SetupError, IntegrationSetupError, RequestUserInput
)
from .config import XboxConfig
from .media_player import XboxRemote
from .auth import XboxAuth

_LOG = logging.getLogger("XBOX_SETUP")

class XboxSetup:
    def __init__(self, api, config: XboxConfig):
        self.api = api
        self.config = config
        self.auth_session = None

    async def handle_command(self, request):
        if isinstance(request, DriverSetupRequest):
            return await self._handle_driver_setup(request)
        elif isinstance(request, UserDataResponse):
            return await self._handle_user_data_response(request)
        elif isinstance(request, AbortDriverSetup):
            await self._cleanup_session()
            return
        return SetupError(IntegrationSetupError.OTHER)

    async def _handle_driver_setup(self, request):
        self.config.liveid = request.setup_data.get("liveid", "").strip()
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.auth_session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=ssl_context)
        )
        auth_handler = XboxAuth(self.auth_session)
        auth_url = auth_handler.generate_auth_url()
        return RequestUserInput(
            {"en": "Xbox Authentication"},
            [
                {"id": "auth_url", "label": {"en": "Login URL"}, "field": {"text": {"value": auth_url, "read_only": True}}},
                {"id": "redirect_url", "label": {"en": "Paste the full redirect URL here"}, "field": {"text": {"value": ""}}},
            ]
        )

    async def _handle_user_data_response(self, request):
        redirect_url = request.input_values.get("redirect_url", "").strip()
        auth_handler = XboxAuth(self.auth_session)
        try:
            tokens = await auth_handler.process_redirect_url(redirect_url)
        finally:
            await self._cleanup_session()
        if not tokens:
            return SetupError(IntegrationSetupError.AUTHORIZATION_ERROR)
        self.config.tokens = tokens
        await self.config.save(self.api)
        try:
            await self.create_xbox_entity()
            return SetupComplete()
        except Exception as e:
            _LOG.exception(f"❌ Failed during Xbox entity creation", exc_info=e)
            return SetupError(IntegrationSetupError.OTHER)

    async def create_xbox_entity(self):
        _LOG.info("🔧 Creating XboxRemote entity...")
        remote_entity = XboxRemote(self.api, self.config)
        self.api.available_entities.add(remote_entity)
        _LOG.info(f"✅ XboxRemote '{remote_entity.name}' registered.")

    async def _cleanup_session(self):
        if self.auth_session and not self.auth_session.closed:
            await self.auth_session.close()