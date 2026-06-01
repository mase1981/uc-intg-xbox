"""
Xbox integration driver.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging

from ucapi_framework import BaseIntegrationDriver

from uc_intg_xbox.config import XboxConfig
from uc_intg_xbox.device import XboxDevice
from uc_intg_xbox.media_player_entity import XboxMediaPlayer
from uc_intg_xbox.remote_entity import XboxRemote
from uc_intg_xbox.sensor_entity import create_sensors

_LOG = logging.getLogger(__name__)

TOKEN_REFRESH_INTERVAL = 12 * 60 * 60


class XboxDriver(BaseIntegrationDriver[XboxDevice, XboxConfig]):
    """Xbox integration driver."""

    def __init__(self):
        super().__init__(
            device_class=XboxDevice,
            entity_classes=[
                XboxMediaPlayer,
                XboxRemote,
                lambda cfg, dev: create_sensors(cfg, dev),
            ],
            driver_id="uc-intg-xbox",
        )
        self._token_refresh_task: asyncio.Task | None = None

    def device_from_entity_id(self, entity_id: str) -> str | None:
        if not entity_id:
            return None
        prefix_end = entity_id.find(".")
        if prefix_end < 0:
            return None
        suffix = entity_id[prefix_end + 1:]
        for device_id in self._device_instances:
            if suffix == device_id or suffix.startswith(device_id + "."):
                return device_id
        if self._config_manager:
            for cfg in self._config_manager.all():
                cfg_id = getattr(cfg, "identifier", None)
                if cfg_id and (suffix == cfg_id or suffix.startswith(cfg_id + ".")):
                    return cfg_id
        return suffix.split(".")[0] if "." in suffix else suffix

    async def on_device_connected(self, device_id: str) -> None:
        await super().on_device_connected(device_id)
        self._start_token_refresh()

    async def on_device_disconnected(self, device_id: str) -> None:
        await super().on_device_disconnected(device_id)

    def _start_token_refresh(self) -> None:
        if self._token_refresh_task and not self._token_refresh_task.done():
            return
        self._token_refresh_task = asyncio.create_task(self._token_refresh_loop())

    async def _token_refresh_loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(TOKEN_REFRESH_INTERVAL)
                for device_id, device in self._device_instances.items():
                    if isinstance(device, XboxDevice) and device.state != "UNAVAILABLE":
                        try:
                            await device.refresh_tokens()
                        except Exception as err:
                            _LOG.warning("Token refresh failed for %s: %s", device_id, err)
            except asyncio.CancelledError:
                break
            except Exception as err:
                _LOG.error("Token refresh loop error: %s", err)
                await asyncio.sleep(60)
