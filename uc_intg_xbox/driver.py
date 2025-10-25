import asyncio
import logging
import os
import ucapi

from uc_intg_xbox.config import XboxConfig
from uc_intg_xbox.setup import XboxSetup
from uc_intg_xbox.media_player import XboxRemote

_LOG = logging.getLogger(__name__)

try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

API = ucapi.IntegrationAPI(loop)

# Global variables for token refresh management
XBOX_REMOTE_ENTITY: XboxRemote | None = None
TOKEN_REFRESH_TASK: asyncio.Task | None = None

@API.listens_to(ucapi.Events.CONNECT)
async def on_connect() -> None:
    """When the UCR2 connects, send the device state and ensure token refresh."""
    await API.set_device_state(ucapi.DeviceStates.CONNECTED)
    # Start token refresh if we have an entity and aren't already refreshing
    if XBOX_REMOTE_ENTITY and (not TOKEN_REFRESH_TASK or TOKEN_REFRESH_TASK.done()):
        start_token_refresh_loop()

def start_token_refresh_loop():
    """Start the token refresh loop to keep authentication alive."""
    global TOKEN_REFRESH_TASK
    if TOKEN_REFRESH_TASK and not TOKEN_REFRESH_TASK.done():
        _LOG.info("Token refresh loop already running.")
        return
    _LOG.info("Starting token refresh loop...")
    TOKEN_REFRESH_TASK = loop.create_task(token_refresh_loop())

async def token_refresh_loop():
    """Periodically refresh Xbox tokens to prevent expiry (every 12 hours)."""
    while True:
        try:
            await asyncio.sleep(12 * 60 * 60)  # Wait 12 hours
            if XBOX_REMOTE_ENTITY:
                _LOG.info("🔄 Performing periodic token refresh...")
                await XBOX_REMOTE_ENTITY.refresh_authentication()
        except Exception as e:
            _LOG.exception("❌ Error during periodic token refresh", exc_info=e)
            await asyncio.sleep(60)  # Wait 1 minute before retrying

class XboxIntegration:
    def __init__(self, api):
        self.api: ucapi.IntegrationAPI = api
        self.config = XboxConfig()
        self.setup = XboxSetup(self.api, self.config)

    async def start(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        _LOG.info("Starting Xbox Integration Driver...")
        driver_path = "driver.json"
        await self.api.init(driver_path, self.setup.handle_command)
        await self.config.load(self.api)
        
        # Ensure entities are available immediately after startup
        await self.ensure_entities_available()
        
        _LOG.info("Driver is up and discoverable.")

    async def ensure_entities_available(self):
        """Ensure Xbox entities are available after startup/reboot with fresh tokens."""
        global XBOX_REMOTE_ENTITY
        
        if self.config.liveid and self.config.tokens:
            entity_id = f"xbox-{self.config.liveid}"
            
            # Check if entity already exists in available entities
            if not self.api.available_entities.contains(entity_id):
                _LOG.info(f"🔄 Creating Xbox entity {entity_id} on startup")
                try:
                    # Create and add the entity
                    remote_entity = XboxRemote(self.api, self.config)
                    self.api.available_entities.add(remote_entity)
                    XBOX_REMOTE_ENTITY = remote_entity  # Store global reference
                    
                    # Initialize device with proactive token refresh (like Xbox Live)
                    asyncio.create_task(remote_entity._init_device())
                    
                    _LOG.info(f"✅ Xbox entity {entity_id} created and available")
                except Exception as e:
                    _LOG.exception(f"❌ Failed to create Xbox entity {entity_id}", exc_info=e)


async def main():
    integration = XboxIntegration(API)
    await integration.start()


if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
        loop.run_forever()
    except KeyboardInterrupt:
        _LOG.info("Driver stopped.")
    finally:
        _LOG.info("Closing the event loop.")
        loop.close()