"""
Xbox sensor entities.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging

from ucapi import sensor
from ucapi_framework import SensorEntity

from uc_intg_xbox.config import XboxConfig
from uc_intg_xbox.device import XboxDevice

_LOG = logging.getLogger(__name__)


class GamertagSensor(SensorEntity):
    """Displays the Xbox gamertag."""

    def __init__(self, device_config: XboxConfig, device: XboxDevice) -> None:
        self._device = device
        entity_id = f"sensor.{device_config.identifier}.gamertag"
        super().__init__(
            entity_id,
            f"{device_config.name} Gamertag",
            [],
            {sensor.Attributes.STATE: sensor.States.UNKNOWN, sensor.Attributes.VALUE: ""},
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: ""},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "UNAVAILABLE":
            self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
            return
        self.update({
            sensor.Attributes.STATE: sensor.States.ON,
            sensor.Attributes.VALUE: self._device.gamertag or "Unknown",
        })


class CurrentGameSensor(SensorEntity):
    """Displays the currently active game or app."""

    def __init__(self, device_config: XboxConfig, device: XboxDevice) -> None:
        self._device = device
        entity_id = f"sensor.{device_config.identifier}.current_game"
        super().__init__(
            entity_id,
            f"{device_config.name} Current Game",
            [],
            {sensor.Attributes.STATE: sensor.States.UNKNOWN, sensor.Attributes.VALUE: ""},
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: ""},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "UNAVAILABLE":
            self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
            return
        self.update({
            sensor.Attributes.STATE: sensor.States.ON,
            sensor.Attributes.VALUE: self._device.media_title or "None",
        })


def create_sensors(config: XboxConfig, device: XboxDevice) -> list:
    return [
        GamertagSensor(config, device),
        CurrentGameSensor(config, device),
    ]
