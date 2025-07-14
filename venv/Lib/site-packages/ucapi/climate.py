"""
Climate entity definitions.

:copyright: (c) 2023 by Unfolded Circle ApS.
:license: MPL-2.0, see LICENSE for more details.
"""

from enum import Enum
from typing import Any

from ucapi.api_definitions import CommandHandler
from ucapi.entity import Entity, EntityTypes


class States(str, Enum):
    """Climate entity states."""

    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"
    OFF = "OFF"
    HEAT = "HEAT"
    COOL = "COOL"
    HEAT_COOL = "HEAT_COOL"
    FAN = "FAN"
    AUTO = "AUTO"


class Features(str, Enum):
    """Climate entity features."""

    ON_OFF = "on_off"
    HEAT = "heat"
    COOL = "cool"
    CURRENT_TEMPERATURE = "current_temperature"
    TARGET_TEMPERATURE = "target_temperature"
    TARGET_TEMPERATURE_RANGE = "target_temperature_range"
    FAN = "fan"


class Attributes(str, Enum):
    """Climate entity attributes."""

    STATE = "state"
    CURRENT_TEMPERATURE = "current_temperature"
    TARGET_TEMPERATURE = "target_temperature"
    TARGET_TEMPERATURE_HIGH = "target_temperature_high"
    TARGET_TEMPERATURE_LOW = "target_temperature_low"
    FAN_MODE = "fan_mode"


class Commands(str, Enum):
    """Climate entity commands."""

    ON = "on"
    OFF = "off"
    HVAC_MODE = "hvac_mode"
    TARGET_TEMPERATURE = "target_temperature"
    TARGET_TEMPERATURE_RANGE = "target_temperature_range"
    FAN_MODE = "fan_mode"


class DeviceClasses(str, Enum):
    """Climate entity device classes."""


class Options(str, Enum):
    """Climate entity options."""

    TEMPERATURE_UNIT = "temperature_unit"
    TARGET_TEMPERATURE_STEP = "target_temperature_step"
    MAX_TEMPERATURE = "max_temperature"
    MIN_TEMPERATURE = "min_temperature"
    FAN_MODES = "fan_modes"


class Climate(Entity):
    """
    Climate entity class.

    See https://github.com/unfoldedcircle/core-api/blob/main/doc/entities/entity_climate.md
    for more information.
    """

    # pylint: disable=R0917
    def __init__(
        self,
        identifier: str,
        name: str | dict[str, str],
        features: list[Features],
        attributes: dict[str, Any],
        device_class: str | None = None,
        options: dict[str, Any] | None = None,
        area: str | None = None,
        cmd_handler: CommandHandler = None,
    ):
        """
        Create a climate-entity instance.

        :param identifier: entity identifier
        :param name: friendly name
        :param features: climate features
        :param attributes: climate attributes
        :param device_class: optional climate device class
        :param options: options
        :param area: optional area
        :param cmd_handler: handler for entity commands
        """
        super().__init__(
            identifier,
            name,
            EntityTypes.CLIMATE,
            features,
            attributes,
            device_class,
            options,
            area,
            cmd_handler,
        )
