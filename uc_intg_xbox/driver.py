import asyncio
import logging
import os
import ucapi # Import the top-level library to check its version
from ucapi import IntegrationAPI
from .config import XboxConfig
from .setup import XboxSetup

# --- Verification Step ---
print("--- UCAPI Library Verification ---")
print(f"ucapi version: {ucapi.__version__}")
try:
    from ucapi import media_player
    print("\nAvailable MediaPlayer Attributes:")
    for attr in dir(media_player.Attributes):
        if not attr.startswith('_'):
            print(f" - {attr}")
    print("\nAvailable MediaPlayer Commands:")
    for command in dir(media_player.Commands):
        if not command.startswith('_'):
            print(f" - {command}")
except ImportError as e:
    print(f"\nCould not import media_player attributes: {e}")
print("---------------------------------")
# --- End Verification Step ---

_LOG = logging.getLogger(__name__)

try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

class XboxIntegration:
    def __init__(self):
        self.api = IntegrationAPI(loop)
        self.config = XboxConfig()
        self.setup = XboxSetup(self.api, self.config)

    async def start(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        _LOG.info("Starting Xbox Integration Driver...")
        driver_path = os.path.join(os.path.dirname(__file__), '..', 'driver.json')
        await self.api.init(driver_path, self.setup.handle_command)
        await self.config.load(self.api)
        _LOG.info("Driver is up and discoverable.")

async def main():
    integration = XboxIntegration()
    await integration.start()

if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
        loop.run_forever()
    except KeyboardInterrupt:
        _LOG.info("Driver stopped.")
    finally:
        loop.close()