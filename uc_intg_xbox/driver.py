import asyncio
import logging
import os
import ucapi

from config import XboxConfig
from setup import XboxSetup
from media_player import XboxRemote

_LOG = logging.getLogger(__name__)

try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

API = ucapi.IntegrationAPI(loop)


@API.listens_to(ucapi.Events.CONNECT)
async def on_connect() -> None:
    """When the UCR2 connects, send the device state and ensure entities are available."""
    await API.set_device_state(ucapi.DeviceStates.CONNECTED)
    
    # Check if we need to recreate entities after reboot
    integration = XboxIntegration(API)
    await integration.ensure_entities_available()


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
        _LOG.info("Driver is up and discoverable.")

    async def ensure_entities_available(self):
        """Ensure Xbox entities are available after startup/reboot"""
        # Load config to check if we have a configured Xbox
        await self.config.load(self.api)
        
        if self.config.liveid and self.config.tokens:
            entity_id = f"xbox-{self.config.liveid}"
            
            # Check if entity already exists in available entities
            if not self.api.available_entities.contains(entity_id):
                _LOG.info(f"🔄 Recreating Xbox entity {entity_id} after restart")
                try:
                    # Create and add the entity
                    remote_entity = XboxRemote(self.api, self.config)
                    self.api.available_entities.add(remote_entity)
                    
                    # Initialize device in background
                    asyncio.create_task(remote_entity._init_device())
                    
                    _LOG.info(f"✅ Xbox entity {entity_id} recreated and available")
                except Exception as e:
                    _LOG.exception(f"❌ Failed to recreate Xbox entity {entity_id}", exc_info=e)


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