"""
Xbox driver module for Unfolded Circle integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
import os
import time
import ucapi
from ucapi import DeviceStates, Events
from ucapi.remote import States as RemoteStates

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
_force_update_event: asyncio.Event = asyncio.Event()
_last_forced_update: float = 0
_delayed_check_task: asyncio.Task | None = None
UPDATE_INTERVAL_ON = 60
UPDATE_INTERVAL_OFF = 90
FORCE_UPDATE_COOLDOWN = 5
DELAYED_CHECK_SECONDS = 15

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

        # Get consoles from config
        consoles = _config.get_consoles()
        if not consoles:
            _LOG.error("No consoles configured")
            _entities_ready = False
            return

        # For v4.1.0, use the first enabled console
        # TODO: Full multi-console UI support in v4.2.0
        active_console = next((c for c in consoles if c.enabled), consoles[0])
        _LOG.info(f"Using console: {active_console.name} ({active_console.liveid})")

        # Temporarily set liveid for XboxClient.from_config
        _config.liveid = active_console.liveid

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
    global _entities_ready, _remote_entity, _media_player_entity, _xbox_client
    
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
    
    console_state = "UNKNOWN"
    if _xbox_client:
        try:
            console_state = await _xbox_client.get_console_state()
            _LOG.info(f"Console initial state: {console_state}")
        except Exception as e:
            _LOG.warning(f"Could not determine console state: {e}")
    
    for entity_id in entity_ids:
        if _remote_entity and entity_id == _remote_entity.id:
            api.configured_entities.add(_remote_entity)
            _LOG.info(f"Remote entity {entity_id} subscribed")
            
            remote_state = RemoteStates.ON if console_state == "ON" else RemoteStates.OFF
            api.configured_entities.update_attributes(_remote_entity.id, {"state": remote_state})
            _LOG.info(f"Remote entity initial state pushed: {remote_state}")
            
        if _media_player_entity and entity_id == _media_player_entity.id:
            api.configured_entities.add(_media_player_entity)
            _LOG.info(f"Media player entity {entity_id} subscribed")
            
            initial_presence = {
                "state": console_state if console_state != "UNKNOWN" else "OFF",
                "title": "Online" if console_state == "ON" else "Offline",
                "image": ""
            }
            await _media_player_entity.update_presence(initial_presence)
            _LOG.info(f"Media player initial state pushed: {console_state}")
            
            start_presence_updates()

def trigger_state_update():
    global _last_forced_update, _force_update_event
    current_time = time.time()
    if current_time - _last_forced_update >= FORCE_UPDATE_COOLDOWN:
        _last_forced_update = current_time
        _force_update_event.set()
        _LOG.debug("State update triggered after command")

async def _delayed_check():
    await asyncio.sleep(DELAYED_CHECK_SECONDS)
    _force_update_event.set()
    _LOG.debug(f"Delayed state check triggered after {DELAYED_CHECK_SECONDS}s")

def trigger_delayed_state_update():
    global _delayed_check_task
    if _delayed_check_task and not _delayed_check_task.done():
        _delayed_check_task.cancel()
    _delayed_check_task = loop.create_task(_delayed_check())

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
    global _xbox_client, _media_player_entity, _remote_entity, _force_update_event
    
    current_interval = UPDATE_INTERVAL_ON
    last_state = "UNKNOWN"
    
    while True:
        try:
            wait_task = asyncio.create_task(asyncio.sleep(current_interval))
            event_task = asyncio.create_task(_force_update_event.wait())
            
            done, pending = await asyncio.wait(
                {wait_task, event_task},
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for task in pending:
                task.cancel()
            
            if event_task in done:
                _force_update_event.clear()
                _LOG.debug("Performing immediate state check after trigger")
            
            if _xbox_client and _xbox_client.client and _media_player_entity:
                _LOG.debug("Fetching Xbox presence data...")
                
                presence_data = await _xbox_client.get_presence_and_title()
                
                if presence_data:
                    current_state = presence_data["state"]
                    
                    await _media_player_entity.update_presence(presence_data)
                    
                    if _remote_entity:
                        if current_state == "OFF":
                            api.configured_entities.update_attributes(_remote_entity.id, {"state": RemoteStates.OFF})
                        else:
                            api.configured_entities.update_attributes(_remote_entity.id, {"state": RemoteStates.ON})
                    
                    if current_state != last_state:
                        _LOG.info(f"Console state changed: {last_state} -> {current_state}")
                        last_state = current_state
                    
                    if current_state == "PLAYING":
                        _LOG.info(f"Now playing: {presence_data['title']}")
                    
                    if current_state == "OFF" and current_interval != UPDATE_INTERVAL_OFF:
                        current_interval = UPDATE_INTERVAL_OFF
                        _LOG.info(f"Console OFF - reducing polling to {UPDATE_INTERVAL_OFF}s")
                    elif current_state in ["ON", "PLAYING"] and current_interval != UPDATE_INTERVAL_ON:
                        current_interval = UPDATE_INTERVAL_ON
                        _LOG.info(f"Console ON - increasing polling to {UPDATE_INTERVAL_ON}s")
                else:
                    _LOG.warning("No presence data returned")
                
            else:
                _LOG.warning("Presence update loop running but client/entity not ready.")
                
        except asyncio.CancelledError:
            break
        except Exception as e:
            _LOG.exception("Error during presence update loop", exc_info=e)
            await asyncio.sleep(10)

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