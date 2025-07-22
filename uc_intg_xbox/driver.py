import asyncio
import logging
import os
import ucapi

from .config import XboxConfig
from .setup import XboxSetup

_LOG = logging.getLogger(__name__)

try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

API = ucapi.IntegrationAPI(loop)

@API.listens_to(ucapi.Events.CONNECT)
async def on_connect() -> None:
    """When the remote connects, send the device state."""
    await API.set_device_state(ucapi.DeviceStates.CONNECTED)

class XboxIntegration:
    def __init__(self, api):
        self.api: ucapi.IntegrationAPI = api
        self.config = XboxConfig()
        self.setup = XboxSetup(self.api, self.config)

    async def start(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        _LOG.info("Starting Xbox Integration Driver...")
        driver_path = os.path.join(os.path.dirname(__file__), '..', 'driver.json')
        
        await self.api.init(driver_path, self.setup.handle_command)
        
        await self.config.load(self.api)
        _LOG.info(f"Driver is up and discoverable, listening on port {API.port}")

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
        loop.close()