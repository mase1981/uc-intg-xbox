"""
Xbox driver module for Unfolded Circle integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
import os
import ucapi
from ucapi import DeviceStates, Events
from ucapi.remote import States as RemoteStates
from ucapi.media_player import States as MediaStates

from uc_intg_xbox.config import XboxConfig
from uc_intg_xbox.setup import XboxSetup
from uc_intg_xbox.remote_entity import XboxRemote
from uc_intg_xbox.media_player_entity import XboxMediaPlayer
from uc_intg_xbox.xbox_client import XboxClient

_LOG = logging.getLogger(__name__)

try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

api: ucapi.IntegrationAPI = ucapi.IntegrationAPI(loop)
_config: XboxConfig | None = None
_xbox_client: XboxClient | None = None
_remote_entity: XboxRemote | None = None
_media_player_entity: XboxMediaPlayer | None = None
_setup_manager: XboxSetup | None = None
_entities_ready: bool = False
_initialization_lock: asyncio.Lock = asyncio.Lock()
_token_refresh_task: asyncio.Task | None = None
_presence_update_task: asyncio.Task | None = None
UPDATE_INTERVAL_SECONDS = 60

async def _initialize_entities():
    global _config, _xbox_client, _remote_entity, _media_player_entity, api, _entities_ready
    
    async with _initialization_lock:
        if _entities_ready:
            _LOG.debug("Entities already initialized, skipping")
            return
            
        if not _config or not _config.is_configured():
            _LOG.info("Integration not configured, skipping entity initialization")
            return
            
        _LOG.info("Initializing entities...")
        
        try:
            _xbox_client, refreshed_tokens = await XboxClient.from_config(_config)
            
            if not _xbox_client:
                _LOG.error("Failed to create Xbox client")
                _entities_ready = False
                return
            
            if refreshed_tokens:
                _config.tokens = refreshed_tokens
                await _config.save(api)
                _LOG.info("Tokens refreshed and saved during entity initialization")
            
            _remote_entity = XboxRemote(api, _xbox_client)
            _media_player_entity = XboxMediaPlayer(api, _xbox_client)
            
            api.available_entities.clear()
            api.available_entities.add(_remote_entity)
            api.available_entities.add(_media_player_entity)
            
            _entities_ready = True
            
            _LOG.info("Entities created and ready for subscription")
            
        except Exception as e:
            _LOG.error("Failed to initialize entities: %s", e)
            _entities_ready = False
            raise

@api.listens_to(Events.CONNECT)
async def on_connect() -> None:
    global _config, _entities_ready
    
    _LOG.info("Remote connected. Checking configuration state...")
    
    if not _config:
        _config = XboxConfig()
    
    config_path = os.path.join(api.config_dir_path, "config.json")
    _config.reload_from_disk(config_path)
    
    if _config.is_configured() and not _entities_ready:
        _LOG.info("Configuration found but entities missing, reinitializing...")
        try:
            await _initialize_entities()
        except Exception as e:
            _LOG.error("Failed to reinitialize entities: %s", e)
            await api.set_device_state(DeviceStates.ERROR)
            return
    
    if _config.is_configured() and _entities_ready:
        await api.set_device_state(DeviceStates.CONNECTED)
        start_token_refresh_loop()
    elif not _config.is_configured():
        await api.set_device_state(DeviceStates.DISCONNECTED)
    else:
        await api.set_device_state(DeviceStates.ERROR)

@api.listens_to(Events.DISCONNECT)
async def on_disconnect() -> None:
    _LOG.info("Remote disconnected")

@api.listens_to(Events.SUBSCRIBE_ENTITIES)
async def on_subscribe_entities(entity_ids: list[str]):
    global _entities_ready, _remote_entity, _media_player_entity
    
    _LOG.info(f"Entities subscription requested: {entity_ids}")
    
    if not _entities_ready:
        _LOG.error("RACE CONDITION: Subscription before entities ready! Attempting recovery...")
        if _config and _config.is_configured():
            await _initialize_entities()
        else:
            _LOG.error("Cannot recover - no configuration available")
            return
    
    available_entity_ids = []
    if _remote_entity:
        available_entity_ids.append(_remote_entity.id)
    if _media_player_entity:
        available_entity_ids.append(_media_player_entity.id)
    
    _LOG.info(f"Available entities: {available_entity_ids}")
    
    for entity_id in entity_ids:
        if _remote_entity and entity_id == _remote_entity.id:
            api.configured_entities.add(_remote_entity)
            _LOG.info(f"Remote entity {entity_id} subscribed")
            api.configured_entities.update_attributes(_remote_entity.id, {"state": RemoteStates.ON})
            _LOG.info(f"Remote entity initial state pushed: ON")
            
        if _media_player_entity and entity_id == _media_player_entity.id:
            api.configured_entities.add(_media_player_entity)
            _LOG.info(f"Media player entity {entity_id} subscribed")
            
            initial_presence = {
                "state": MediaStates.OFF,
                "title": "Offline",
                "image": ""
            }
            await _media_player_entity.update_presence(initial_presence)
            _LOG.info(f"Media player initial state pushed: OFF")
            
            start_presence_updates()

def start_token_refresh_loop():
    global _token_refresh_task
    if _token_refresh_task and not _token_refresh_task.done():
        _LOG.info("Token refresh loop already running.")
        return
    _LOG.info("Starting token refresh loop...")
    _token_refresh_task = loop.create_task(token_refresh_loop())

async def token_refresh_loop():
    global _config, _xbox_client
    while True:
        try:
            await asyncio.sleep(12 * 60 * 60)
            if _xbox_client and _config:
                _LOG.info("Performing periodic token refresh...")
                refreshed_client, refreshed_tokens = await XboxClient.from_config(
                    _config, _xbox_client.session
                )
                if refreshed_client and refreshed_tokens:
                    _config.tokens = refreshed_tokens
                    await _config.save(api)
                    _LOG.info("Tokens refreshed successfully")
        except Exception as e:
            _LOG.exception("Error during periodic token refresh", exc_info=e)
            await asyncio.sleep(60)

def start_presence_updates():
    global _presence_update_task
    if _presence_update_task and not _presence_update_task.done():
        _LOG.info("Presence update loop already running.")
        return
    _LOG.info("Starting presence update loop...")
    _presence_update_task = loop.create_task(presence_update_loop())

async def presence_update_loop():
    global _xbox_client, _media_player_entity
    
    while True:
        try:
            if _xbox_client and _xbox_client.client and _media_player_entity:
                _LOG.debug("Fetching Xbox presence data...")
                
                presence = await _xbox_client.get_presence()
                console_status = await _xbox_client.get_console_status()
                
                if not presence:
                    await asyncio.sleep(UPDATE_INTERVAL_SECONDS)
                    continue
                
                presence_data = {
                    "state": MediaStates.OFF,
                    "title": "Offline",
                    "image": ""
                }
                
                if presence.presence_state == "Online":
                    if console_status and console_status.focus_app_aumid:
                        if presence.presence_text and presence.presence_text != "Home":
                            presence_data["state"] = MediaStates.PLAYING
                            presence_data["title"] = presence.presence_text
                            _LOG.info(f"Now playing: {presence.presence_text}")
                        else:
                            presence_data["state"] = MediaStates.ON
                            presence_data["title"] = "Home"
                    else:
                        presence_data["state"] = MediaStates.ON
                        presence_data["title"] = "Home"
                
                await _media_player_entity.update_presence(presence_data)
                
            else:
                _LOG.warning("Presence update loop running but client/entity not ready.")
                
        except Exception as e:
            _LOG.exception("Error during presence update loop", exc_info=e)
            
        await asyncio.sleep(UPDATE_INTERVAL_SECONDS)

async def setup_handler(msg: ucapi.SetupAction) -> ucapi.SetupAction:
    global _config, _entities_ready, _setup_manager
    
    if not _config:
        _config = XboxConfig()
    
    if not _setup_manager:
        _setup_manager = XboxSetup(api, _config)
    
    action = await _setup_manager.handle_command(msg)
    
    if isinstance(action, ucapi.SetupComplete):
        _LOG.info("Setup confirmed. Initializing integration components...")
        await _initialize_entities()
        if _entities_ready:
            await api.set_device_state(DeviceStates.CONNECTED)
            start_token_refresh_loop()
    
    return action

class XboxIntegration:
    def __init__(self, integration_api):
        self.api: ucapi.IntegrationAPI = integration_api
        global _config
        _config = XboxConfig()

    async def start(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        _LOG.info("Starting Xbox Integration Driver...")
        
        driver_path = "driver.json"
        await self.api.init(driver_path, setup_handler)
        await _config.load(self.api)
        
        if _config.is_configured():
            _LOG.info("Found existing configuration, pre-initializing entities for reboot survival")
            loop.create_task(_initialize_entities())
        
        _LOG.info("Driver is up and discoverable.")

async def main():
    integration = XboxIntegration(api)
    await integration.start()

if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
        loop.run_forever()
    except KeyboardInterrupt:
        _LOG.info("Driver stopped.")
    finally:
        _LOG.info("Closing the event loop.")
        if _xbox_client:
            loop.run_until_complete(_xbox_client.close())
        loop.close()