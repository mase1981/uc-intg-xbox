import logging
from xbox.webapi.api.client import XboxLiveClient

_LOG = logging.getLogger(__name__)

class XboxDevice:
    """Represents the Xbox console and handles all communication with it."""
    def __init__(self, client: XboxLiveClient, live_id: str):
        self.client = client
        self.live_id = live_id

    async def turn_on(self):
        _LOG.info(f"Sending power on to {self.live_id}")
        await self.client.smartglass.turn_on(self.live_id)

    async def turn_off(self):
        _LOG.info(f"Sending power off to {self.live_id}")
        await self.client.smartglass.turn_off(self.live_id)