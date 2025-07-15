import asyncio
import logging
import os
from ucapi import IntegrationAPI
from .config import XboxConfig
from .setup import XboxSetup

_LOG = logging.getLogger(__name__)

# This is the correct event loop boilerplate for ucapi v0.3.1
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

class XboxIntegration:
    def __init__(self):
        # CORRECTED: IntegrationAPI constructor for this version only takes the loop.
        self.api = IntegrationAPI(loop)
        self.config = XboxConfig()
        self.setup = XboxSetup(self.api, self.config)

    async def start(self):
        """Initializes the integration and starts listening."""
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        _LOG.info("Starting Xbox Integration Driver...")
        
        driver_path = os.path.join(os.path.dirname(__file__), '..', 'driver.json')

        # CORRECTED: We pass the setup handler to the init() method.
        # This is the correct pattern for this library version.
        await self.api.init(driver_path, self.setup.handle_command)
        await self.config.load(self.api)
        
        _LOG.info("Driver is up and discoverable.")

async def main():
    """The main entry point for the integration driver."""
    integration = XboxIntegration()
    await integration.start()

# --- This is the corrected event loop execution based on your original file ---
if __name__ == "__main__":
    try:
        # Run the main setup function to get everything started
        loop.run_until_complete(main())
        # Then, run the loop forever to keep the server alive
        loop.run_forever()
    except KeyboardInterrupt:
        _LOG.info("Driver stopped.")
    finally:
        _LOG.info("Closing the event loop.")
        loop.close()