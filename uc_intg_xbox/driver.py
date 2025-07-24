import asyncio
import logging
import os
import ucapi

from config import XboxConfig
from setup import XboxSetup

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
    """When the UCR2 connects, send the device state."""
    # This example is ready all the time!
    await API.set_device_state(ucapi.DeviceStates.CONNECTED)


class XboxIntegration:
    def __init__(self, api):
        self.api: ucapi.IntegrationAPI = api
        self.config = XboxConfig()
        self.setup = XboxSetup(self.api, self.config)
        self.update_task: asyncio.Task | None = None

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
        self.start_presence_updates()

    def start_presence_updates(self):
        """Starts the background presence update loop."""
        if self.update_task:
            self.update_task.cancel()
        _LOG.info(f"Starting presence update loop (every {UPDATE_INTERVAL_SECONDS}s).")
        self.update_task = loop.create_task(self.presence_update_loop())

    async def presence_update_loop(self):
        """Periodically fetches Xbox presence and updates the entity."""
        await asyncio.sleep(10) # Initial delay to allow entities to be created
        while True:
            try:
                # Check if the entity and client exist before fetching
                if self.setup.entity and self.setup.entity.device:
                    client = self.setup.entity.device.client
                    _LOG.info("Fetching Xbox presence...")
                    presence = await client.presence.get_presence(client.xuid)

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

                    self.setup.entity.update_presence(game_info)
                else:
                    _LOG.debug("Entity or client not ready, skipping presence check.")
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
        _LOG.info("Driver stopped.")
    finally:
        _LOG.info("Closing the event loop.")
        loop.close()
