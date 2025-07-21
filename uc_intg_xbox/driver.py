import asyncio
import logging
import os
import argparse  # Import the argument parsing library
import ucapi

from .config import XboxConfig
from .setup import XboxSetup

_LOG = logging.getLogger(__name__)

# 1. Set up an argument parser to read the --port argument from the remote
parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, help="Port to listen on", default=0)
args = parser.parse_args()

try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# 2. Pass the port from the arguments when creating the API object
API = ucapi.IntegrationAPI(loop, port=args.port)

@API.listens_to(ucapi.Events.CONNECT)
async def on_connect() -> None:
    """When the UCR connects, send the device state."""
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
        # Log the port we are actually using
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
        _LOG.info("Closing the event loop.")
        loop.close()