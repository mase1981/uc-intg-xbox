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
_console_instances: dict = {}  # Map liveid -> {client, remote, media_player}
_setup_manager: XboxSetup | None = None
_entities_ready: bool = False
_initialization_lock: asyncio.Lock = asyncio.Lock()
_token_refresh_task: asyncio.Task | None = None
_presence_update_tasks: dict = {}  # Map liveid -> task
_force_update_events: dict = {}  # Map liveid -> event
_last_forced_updates: dict = {}  # Map liveid -> timestamp
_delayed_check_tasks: dict = {}  # Map liveid -> task
UPDATE_INTERVAL_ON = 60
UPDATE_INTERVAL_OFF = 90
FORCE_UPDATE_COOLDOWN = 5
DELAYED_CHECK_SECONDS = 15

async def _initialize_entities():
    global _config, _console_instances, api, _entities_ready, _force_update_events

    async with _initialization_lock:
        if _entities_ready:
            _LOG.debug("Entities already initialized, skipping")
            return

        if not _config or not _config.is_configured():
            _LOG.info("Integration not configured, skipping entity initialization")
            return

        _LOG.info("Initializing entities for all consoles...")

        # Get consoles from config
        consoles = _config.get_consoles()
        if not consoles:
            _LOG.error("No consoles configured")
            _entities_ready = False
            return

        api.available_entities.clear()
        _console_instances.clear()

        # Create entities for each console
        for console in consoles:
            if not console.enabled:
                _LOG.info(f"Skipping disabled console: {console.name}")
                continue

            _LOG.info(f"Initializing console: {console.name} ({console.liveid})")

            # Temporarily set liveid for XboxClient.from_config
            _config.liveid = console.liveid

            try:
                xbox_client, refreshed_tokens = await XboxClient.from_config(_config)

                if not xbox_client:
                    _LOG.error(f"Failed to create Xbox client for {console.name}")
                    continue

                if refreshed_tokens:
                    _config.tokens = refreshed_tokens
                    await _config.save(api)
                    _LOG.info(f"Tokens refreshed and saved for {console.name}")

                # Create entities with unique IDs based on console name/liveid
                remote_entity = XboxRemote(api, xbox_client, console.name, console.liveid)
                media_player_entity = XboxMediaPlayer(api, xbox_client, console.name, console.liveid)

                api.available_entities.add(remote_entity)
                api.available_entities.add(media_player_entity)

                # Store console instance
                _console_instances[console.liveid] = {
                    "client": xbox_client,
                    "remote": remote_entity,
                    "media_player": media_player_entity,
                    "name": console.name
                }

                # Initialize force update event for this console
                _force_update_events[console.liveid] = asyncio.Event()
                _last_forced_updates[console.liveid] = 0

                _LOG.info(f"Entities created for {console.name}: Remote={remote_entity.id}, MediaPlayer={media_player_entity.id}")

            except Exception as e:
                _LOG.error(f"Failed to initialize entities for {console.name}: {e}")
                continue

        # Clear temporary liveid
        _config.liveid = None

        if _console_instances:
            _entities_ready = True
            _LOG.info(f"Successfully initialized {len(_console_instances)} console(s)")
        else:
            _LOG.error("No consoles were successfully initialized")
            _entities_ready = False

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
    global _entities_ready, _console_instances

    _LOG.info(f"Entities subscription requested: {entity_ids}")

    if not _entities_ready:
        _LOG.error("RACE CONDITION: Subscription before entities ready! Attempting recovery...")
        if _config and _config.is_configured():
            await _initialize_entities()
        else:
            _LOG.error("Cannot recover - no configuration available")
            return

    # Process subscription for each requested entity
    for entity_id in entity_ids:
        # Find which console this entity belongs to
        for liveid, instance in _console_instances.items():
            remote_entity = instance["remote"]
            media_player_entity = instance["media_player"]
            xbox_client = instance["client"]

            # Check if this is the remote entity
            if entity_id == remote_entity.id:
                api.configured_entities.add(remote_entity)
                _LOG.info(f"Remote entity {entity_id} subscribed for console {instance['name']}")

                try:
                    console_state = await xbox_client.get_console_state()
                    remote_state = RemoteStates.ON if console_state == "ON" else RemoteStates.OFF
                    api.configured_entities.update_attributes(remote_entity.id, {"state": remote_state})
                    _LOG.info(f"Remote entity initial state pushed: {remote_state}")
                except Exception as e:
                    _LOG.warning(f"Could not determine console state: {e}")

            # Check if this is the media player entity
            elif entity_id == media_player_entity.id:
                api.configured_entities.add(media_player_entity)
                _LOG.info(f"Media player entity {entity_id} subscribed for console {instance['name']}")

                try:
                    console_state = await xbox_client.get_console_state()
                    initial_presence = {
                        "state": console_state if console_state != "UNKNOWN" else "OFF",
                        "title": "Online" if console_state == "ON" else "Offline",
                        "image": ""
                    }
                    await media_player_entity.update_presence(initial_presence)
                    _LOG.info(f"Media player initial state pushed: {console_state}")
                except Exception as e:
                    _LOG.warning(f"Could not determine console state: {e}")

                # Start presence updates for this console
                start_presence_updates(liveid)

def trigger_state_update(liveid: str):
    """Trigger immediate state update for specific console."""
    global _last_forced_updates, _force_update_events
    current_time = time.time()
    if current_time - _last_forced_updates.get(liveid, 0) >= FORCE_UPDATE_COOLDOWN:
        _last_forced_updates[liveid] = current_time
        if liveid in _force_update_events:
            _force_update_events[liveid].set()
            _LOG.debug(f"State update triggered for console {liveid}")

async def _delayed_check(liveid: str):
    """Delayed state check for specific console."""
    await asyncio.sleep(DELAYED_CHECK_SECONDS)
    if liveid in _force_update_events:
        _force_update_events[liveid].set()
        _LOG.debug(f"Delayed state check triggered for console {liveid} after {DELAYED_CHECK_SECONDS}s")

def trigger_delayed_state_update(liveid: str):
    """Trigger delayed state update for specific console."""
    global _delayed_check_tasks
    if liveid in _delayed_check_tasks and not _delayed_check_tasks[liveid].done():
        _delayed_check_tasks[liveid].cancel()
    _delayed_check_tasks[liveid] = loop.create_task(_delayed_check(liveid))

def start_token_refresh_loop():
    global _token_refresh_task
    if _token_refresh_task and not _token_refresh_task.done():
        _LOG.info("Token refresh loop already running.")
        return
    _LOG.info("Starting token refresh loop...")
    _token_refresh_task = loop.create_task(token_refresh_loop())

async def token_refresh_loop():
    """Periodic token refresh for all consoles."""
    global _config, _console_instances
    while True:
        try:
            await asyncio.sleep(12 * 60 * 60)
            if _console_instances and _config:
                _LOG.info("Performing periodic token refresh for all consoles...")
                # Get any client session for token refresh
                first_instance = next(iter(_console_instances.values()), None)
                if first_instance:
                    xbox_client = first_instance["client"]
                    refreshed_client, refreshed_tokens = await XboxClient.from_config(
                        _config, xbox_client.session
                    )
                    if refreshed_client and refreshed_tokens:
                        _config.tokens = refreshed_tokens
                        await _config.save(api)
                        _LOG.info("Tokens refreshed successfully for all consoles")
        except Exception as e:
            _LOG.exception("Error during periodic token refresh", exc_info=e)
            await asyncio.sleep(60)

def start_presence_updates(liveid: str):
    """Start presence update loop for specific console."""
    global _presence_update_tasks
    if liveid in _presence_update_tasks and not _presence_update_tasks[liveid].done():
        _LOG.info(f"Presence update loop already running for console {liveid}")
        return
    _LOG.info(f"Starting presence update loop for console {liveid}...")
    _presence_update_tasks[liveid] = loop.create_task(presence_update_loop(liveid))

async def presence_update_loop(liveid: str):
    """Presence update loop for specific console."""
    global _console_instances, _force_update_events

    if liveid not in _console_instances:
        _LOG.error(f"Console {liveid} not found in instances")
        return

    instance = _console_instances[liveid]
    xbox_client = instance["client"]
    media_player_entity = instance["media_player"]
    remote_entity = instance["remote"]
    console_name = instance["name"]
    force_event = _force_update_events[liveid]

    current_interval = UPDATE_INTERVAL_ON
    last_state = "UNKNOWN"

    _LOG.info(f"Presence update loop started for {console_name}")

    while True:
        try:
            wait_task = asyncio.create_task(asyncio.sleep(current_interval))
            event_task = asyncio.create_task(force_event.wait())

            done, pending = await asyncio.wait(
                {wait_task, event_task},
                return_when=asyncio.FIRST_COMPLETED
            )

            for task in pending:
                task.cancel()

            if event_task in done:
                force_event.clear()
                _LOG.debug(f"Performing immediate state check for {console_name}")

            if xbox_client and xbox_client.client and media_player_entity:
                _LOG.debug(f"Fetching presence data for {console_name}...")

                presence_data = await xbox_client.get_presence_and_title()

                if presence_data:
                    current_state = presence_data["state"]

                    await media_player_entity.update_presence(presence_data)

                    if remote_entity:
                        if current_state == "OFF":
                            api.configured_entities.update_attributes(remote_entity.id, {"state": RemoteStates.OFF})
                        else:
                            api.configured_entities.update_attributes(remote_entity.id, {"state": RemoteStates.ON})

                    if current_state != last_state:
                        _LOG.info(f"{console_name} state changed: {last_state} -> {current_state}")
                        last_state = current_state

                    if current_state == "PLAYING":
                        _LOG.info(f"{console_name} now playing: {presence_data['title']}")

                    if current_state == "OFF" and current_interval != UPDATE_INTERVAL_OFF:
                        current_interval = UPDATE_INTERVAL_OFF
                        _LOG.info(f"{console_name} OFF - reducing polling to {UPDATE_INTERVAL_OFF}s")
                    elif current_state in ["ON", "PLAYING"] and current_interval != UPDATE_INTERVAL_ON:
                        current_interval = UPDATE_INTERVAL_ON
                        _LOG.info(f"{console_name} ON - increasing polling to {UPDATE_INTERVAL_ON}s")
                else:
                    _LOG.warning(f"No presence data returned for {console_name}")

            else:
                _LOG.warning(f"Presence update loop running but client/entity not ready for {console_name}")

        except asyncio.CancelledError:
            _LOG.info(f"Presence update loop cancelled for {console_name}")
            break
        except Exception as e:
            _LOG.exception(f"Error during presence update loop for {console_name}", exc_info=e)
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
        # Close all Xbox clients
        for instance in _console_instances.values():
            if instance["client"]:
                loop.run_until_complete(instance["client"].close())
        loop.close()