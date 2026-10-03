"""
Xbox sensor entities.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Callable

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


class XboxValueSensor(SensorEntity):
    """A sensor whose value is read from the device on every update."""

    def __init__(
        self,
        device_config: XboxConfig,
        device: XboxDevice,
        key: str,
        label: str,
        value: Callable[[XboxDevice], Any],
        unit: str = "",
    ) -> None:
        self._device = device
        self._value = value
        super().__init__(
            f"sensor.{device_config.identifier}.{key}",
            f"{device_config.name} {label}",
            [],
            {sensor.Attributes.STATE: sensor.States.UNKNOWN, sensor.Attributes.VALUE: ""},
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: unit},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "UNAVAILABLE":
            self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
            return
        try:
            value = self._value(self._device)
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.debug("[%s] Sensor value failed: %s", self.id, err)
            value = None
        if value is None or value == "":
            # Not known yet, or nothing to report (no game running): keep the tile readable.
            self.update({sensor.Attributes.STATE: sensor.States.ON, sensor.Attributes.VALUE: "-"})
            return
        self.update({sensor.Attributes.STATE: sensor.States.ON, sensor.Attributes.VALUE: value})


# ----------------------------------------------------------------------
# Values
# ----------------------------------------------------------------------
def _profile(device: XboxDevice, key: str) -> Any:
    return (device.profile or {}).get(key)


def _progress(device: XboxDevice, key: str) -> Any:
    return (device.progress or {}).get(key)


def _last_online(device: XboxDevice) -> str | None:
    profile = device.profile or {}
    if profile.get("online"):
        return "Online now"
    last_seen = profile.get("last_seen")
    if not isinstance(last_seen, datetime):
        return None
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)
    seconds = max(0, int((datetime.now(timezone.utc) - last_seen).total_seconds()))
    if seconds < 60:
        return "Just now"
    if seconds < 3600:
        return f"{seconds // 60} min ago"
    if seconds < 86400:
        return f"{seconds // 3600} h ago"
    days = seconds // 86400
    return "1 day ago" if days == 1 else f"{days} days ago"


def _in_party(device: XboxDevice) -> str | None:
    in_party = _profile(device, "in_party")
    if in_party is None:
        return None
    if not in_party:
        return "No"
    restriction = _profile(device, "join_restriction")
    return f"Yes ({restriction})" if restriction else "Yes"


def _storage_gb(device: XboxDevice, key: str) -> float | None:
    """Summed over all drives (internal and external), in GB."""
    drives = device.storage
    if not drives:
        return None
    total = sum(drive.get(key) or 0 for drive in drives)
    return round(total / 1_000_000_000, 1)


def create_sensors(config: XboxConfig, device: XboxDevice) -> list:
    def value(key, label, getter, unit=""):
        return XboxValueSensor(config, device, key, label, getter, unit)

    return [
        GamertagSensor(config, device),
        CurrentGameSensor(config, device),
        value("status", "Status", lambda d: _profile(d, "status")),
        value("gamerscore", "Gamerscore", lambda d: _profile(d, "gamerscore"), "G"),
        value("platform", "Platform", lambda d: _profile(d, "platform")),
        value("achievements", "Achievements", lambda d: _progress(d, "achievements")),
        value("title_gamerscore", "Game Gamerscore", lambda d: _progress(d, "gamerscore"), "G"),
        value("game_progress", "Game Progress", lambda d: _progress(d, "progress"), "%"),
        value("last_online", "Last Online", _last_online),
        value("friends_online", "Friends Online", lambda d: d.friends_online),
        value("followers", "Followers", lambda d: _profile(d, "followers")),
        value("following", "Following", lambda d: _profile(d, "following")),
        value("in_party", "In Party", _in_party),
        value("storage_free", "Free Storage", lambda d: _storage_gb(d, "free"), "GB"),
        value("storage_total", "Total Storage", lambda d: _storage_gb(d, "total"), "GB"),
    ]
