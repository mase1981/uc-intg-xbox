import logging
import httpx
import ssl
import certifi
import re
from ucapi import (
    DriverSetupRequest,
    UserDataResponse,
    AbortDriverSetup,
    SetupComplete,
    SetupError,
    IntegrationSetupError,
    RequestUserInput,
)
from config import XboxConfig
from media_player import XboxRemote
from presence_entity import XboxPresenceMediaPlayer
from auth import XboxAuth
from xbox_device import XboxDevice

_LOG = logging.getLogger("XBOX_SETUP")


async def fix_microsoft_timestamps(response):
    if "user.auth.xboxlive.com" in str(response.url):
        await response.aread()
        response_text = response.text
        fixed_text = re.sub(r"(\.\d{6})\d+Z", r"\1Z", response_text)
        response._content = fixed_text.encode("utf-8")


class XboxSetup:
    def __init__(self, api, config: XboxConfig):
        self.api = api
        self.config = config
        self.auth_session: httpx.AsyncClient | None = None
        self.remote_entity: XboxRemote | None = None
        self.presence_entity: XboxPresenceMediaPlayer | None = None

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
        self.auth_session = httpx.AsyncClient(
            verify=ssl_context, event_hooks={"response": [fix_microsoft_timestamps]}
        )

        auth_handler = XboxAuth(self.auth_session)
        auth_url = auth_handler.generate_auth_url()
        return RequestUserInput(
            {"en": "Xbox Authentication"},
            [
                {"id": "auth_url", "label": {"en": "Login URL"}, "field": {"text": {"value": auth_url, "read_only": True}}},
                {"id": "redirect_url", "label": {"en": "Paste the full redirect URL here"}, "field": {"text": {"value": ""}}},
            ],
        )

    async def _handle_user_data_response(self, request):
        redirect_url = request.input_values.get("redirect_url", "").strip()
        auth_handler = XboxAuth(self.auth_session)
        try:
            tokens = await auth_handler.process_redirect_url(redirect_url)
        finally:
            # We keep the session open for the create_xbox_entities step
            pass
        
        if not tokens:
            await self._cleanup_session()
            return SetupError(IntegrationSetupError.AUTHORIZATION_ERROR)
        
        self.config.tokens = tokens
        await self.config.save(self.api)
        
        try:
            await self.create_xbox_entities()
            return SetupComplete()
        except Exception as e:
            _LOG.exception(f"❌ Failed during entity creation", exc_info=e)
            return SetupError(IntegrationSetupError.OTHER)
        finally:
            await self._cleanup_session()

    async def create_xbox_entities(self):
        """Creates and registers both entities."""
        # Create and register the remote entity
        if not self.remote_entity:
            self.remote_entity = XboxRemote(self.api, self.config)
            self.api.available_entities.add(self.remote_entity)

        # Create and register the presence entity
        if not self.presence_entity:
            client, _ = await XboxDevice.from_config(self.config, self.auth_session)
            if client:
                profile = await client.client.profile.get_profile_by_xuid(client.client.xuid)
                
                gamertag = "Xbox User"
                for setting in profile.profile_users[0].settings:
                    if setting.id == "ModernGamertag":
                        gamertag = setting.value
                        break
                
                self.presence_entity = XboxPresenceMediaPlayer(self.api, self.config.liveid, gamertag)
                self.api.available_entities.add(self.presence_entity)

    async def _cleanup_session(self):
        if self.auth_session and not self.auth_session.is_closed:
            await self.auth_session.aclose()