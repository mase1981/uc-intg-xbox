"""
Sensor entity definitions.

:copyright: (c) 2023 by Unfolded Circle ApS.
:license: MPL-2.0, see LICENSE for more details.
"""

from enum import Enum
from typing import Any

from ucapi.entity import Entity, EntityTypes


class States(str, Enum):
    """Sensor entity states."""

    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"
    ON = "ON"


class Features(str, Enum):
    """Sensor entity features."""


class Attributes(str, Enum):
    """Sensor entity attributes."""

    STATE = "state"
    VALUE = "value"
    UNIT = "unit"


class Commands(str, Enum):
    """Sensor entity commands."""


class DeviceClasses(str, Enum):
    """Sensor entity device classes."""

    CUSTOM = "custom"
    BATTERY = "battery"
    CURRENT = "current"
    ENERGY = "energy"
    HUMIDITY = "humidity"
    POWER = "power"
    TEMPERATURE = "temperature"
    VOLTAGE = "voltage"


class Options(str, Enum):
    """Sensor entity options."""

    CUSTOM_UNIT = "custom_unit"
    NATIVE_UNIT = "native_unit"
    DECIMALS = "decimals"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"


class Sensor(Entity):
    """
    Sensor entity class.

    See https://github.com/unfoldedcircle/core-api/blob/main/doc/entities/entity_sensor.md
    for more information.
    """

    # pylint: disable=R0917
    def __init__(
        self,
        identifier: str,
        name: str | dict[str, str],
        features: list[Features],
        attributes: dict[str, Any],
        device_class: DeviceClasses | None = None,
        options: dict[str, Any] | None = None,
        area: str | None = None,
    ):
        """
        Create sensor-entity instance.

        :param identifier: entity identifier
        :param name: friendly name
        :param features: sensor features
        :param attributes: sensor attributes
        :param device_class: optional sensor device class
        :param options: options
        :param area: optional area
        """
        super().__init__(
            identifier,
            name,
            EntityTypes.SENSOR,
            features,
            attributes,
            device_class,
            options,
            area,
        )
