import asyncio
import logging
import traceback
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
from media_player import XboxRemote
from presence_entity import XboxPresenceMediaPlayer

_LOG = logging.getLogger(__name__)
UPDATE_INTERVAL_SECONDS = 60

try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

API = ucapi.IntegrationAPI(loop)

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
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        _LOG.info("Starting Xbox Integration Driver...")
        driver_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "driver.json"))
        await self.api.init(driver_path, self.setup.handle_command)
        await self.config.load(self.api)
        _LOG.info("Driver is up and discoverable.")
        await self.connect_and_create_entities()

    async def connect_and_create_entities(self):
        if not self.config.tokens or not self.config.liveid:
            return

        _LOG.info("Attempting to authenticate from existing config...")
        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            self.http_session = httpx.AsyncClient(verify=ssl_context)

            auth_mgr = AuthenticationManager(self.http_session, CLIENT_ID, CLIENT_SECRET, "")
            auth_mgr.oauth = OAuth2TokenResponse.model_validate(self.config.tokens)
            await auth_mgr.refresh_tokens()

            self.config.tokens = auth_mgr.oauth.model_dump()
            await self.config.save(self.api)

            self.client = XboxLiveClient(auth_mgr)
            _LOG.info("✅ Successfully authenticated with Xbox Live.")
            await self.api.set_device_state(ucapi.DeviceStates.CONNECTED)

            profile = await self.client.profile.get_profile_by_xuid(self.client.xuid)
            gamertag = profile.profile_users[0].settings.get_setting_by_id("ModernGamertag").value

            # Create and register both entities on startup
            if not self.setup.remote_entity:
                self.setup.remote_entity = XboxRemote(self.api, self.config)
                self.api.available_entities.add(self.setup.remote_entity)

            if not self.setup.presence_entity:
                self.setup.presence_entity = XboxPresenceMediaPlayer(self.api, self.config.liveid, gamertag)
                self.api.available_entities.add(self.setup.presence_entity)

            self.start_presence_updates()

        except Exception as e:
            _LOG.exception("Failed to authenticate or create entities on startup", exc_info=e)
            if self.http_session: await self.http_session.aclose()

    def start_presence_updates(self):
        if self.update_task:
            self.update_task.cancel()
        self.update_task = loop.create_task(self.presence_update_loop())

    async def presence_update_loop(self):
        _LOG.info(f"Starting presence update loop (will refresh every {UPDATE_INTERVAL_SECONDS}s).")
        await asyncio.sleep(10)
        while True:
            try:
                if self.setup.presence_entity and self.client:
                    _LOG.info("Fetching Xbox presence...")
                    presence = await self.client.presence.get_presence(self.client.xuid)

                    game_info = {"state": presence.state}
                    if presence.state.lower() == "online" and presence.title_records:
                        active_title = presence.title_records[0]
                        game_info["title"] = active_title.name
                        for item in active_title.display_image:
                            if item.type == "Icon":
                                game_info["image"] = item.url
                                break
                    else:
                        game_info["title"] = "Home" if presence.state.lower() == "online" else "Offline"
                        game_info["image"] = None

                    self.setup.presence_entity.update_presence(game_info)
                else:
                    _LOG.debug("Presence entity or client not ready, skipping presence check.")
            except Exception as e:
                _LOG.exception("❌ Error during presence update loop", exc_info=e)

            await asyncio.sleep(UPDATE_INTERVAL_SECONDS)


async def main():
    integration = XboxIntegration(API)
    await integration.start()


if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
        loop.run_forever()
    except KeyboardInterrupt:
        _LOG.info("Driver stopped by user.")
    finally:
        _LOG.info("Closing the event loop and shutting down API.")
        traceback.print_exc()
        if 'API' in globals() and API.is_running():
            loop.run_until_complete(API.stop())

        if 'integration' in locals() and integration.http_session and not integration.http_session.is_closed:
            loop.run_until_complete(integration.http_session.aclose())
        loop.close()