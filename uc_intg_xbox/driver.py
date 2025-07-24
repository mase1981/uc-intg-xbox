import asyncio
import logging
import os
import ucapi
import httpx
import ssl
import certifi
from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.authentication.models import OAuth2TokenResponse
from xbox.webapi.scripts import CLIENT_ID, CLIENT_SECRET

from config import XboxConfig
from setup import XboxSetup

_LOG = logging.getLogger(__name__)
UPDATE_INTERVAL_SECONDS = 60

# ... (loop and API setup remain the same) ...

@API.listens_to(ucapi.Events.CONNECT)
async def on_connect() -> None:
    await API.set_device_state(ucapi.DeviceStates.CONNECTED)

class XboxIntegration:
    def __init__(self, api):
        self.api: ucapi.IntegrationAPI = api
        self.config = XboxConfig()
        self.setup = XboxSetup(self.api, self.config)
        self.update_task: asyncio.Task | None = None
        self.client: XboxLiveClient | None = None
        self.http_session: httpx.AsyncClient | None = None

    async def start(self):
        # ... (logging setup and api.init remain the same) ...
        await self.config.load(self.api)
        _LOG.info("Driver is up and discoverable.")
        await self.connect_and_create_entities()

    async def connect_and_create_entities(self):
        if not self.config.tokens or not self.config.liveid:
            return

        _LOG.info("Attempting to authenticate...")
        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            self.http_session = httpx.AsyncClient(verify=ssl_context)

            auth_mgr = AuthenticationManager(self.http_session, CLIENT_ID, CLIENT_SECRET, "")
            auth_mgr.oauth = OAuth2TokenResponse.model_validate(self.config.tokens)
            await auth_mgr.refresh_tokens()

            self.config.tokens = auth_mgr.oauth.model_dump()
            await self.config.save(self.api)

            self.client = XboxLiveClient(auth_mgr)

            _LOG.info("Fetching profile to get gamertag...")
            profile = await self.client.profile.get_profile_by_xuid(self.client.xuid)
            gamertag = profile.profile_users[0].settings.get_setting_by_id("ModernGamertag").value

            # Create both entities
            if not self.setup.remote_entity:
                self.setup.remote_entity = self.setup.XboxRemote(self.api, self.config)
                self.api.available_entities.add(self.setup.remote_entity)
                self.api.configured_entities.add(self.setup.remote_entity)

            if not self.setup.presence_entity:
                self.setup.presence_entity = self.setup.XboxPresenceMediaPlayer(self.api, self.config.liveid, gamertag)
                self.api.available_entities.add(self.setup.presence_entity)
                self.api.configured_entities.add(self.setup.presence_entity)

            self.start_presence_updates()

        except Exception:
            _LOG.exception("Failed to authenticate or create entities")
            if self.http_session: await self.http_session.aclose()

    def start_presence_updates(self):
        # ... (this method remains the same) ...

    async def presence_update_loop(self):
        # ... (this method remains the same, but updates self.setup.presence_entity) ...
        if self.setup.presence_entity and self.client:
            # ... fetch presence ...
            self.setup.presence_entity.update_presence(game_info)

# ... (main and __main__ block remain the same) ...