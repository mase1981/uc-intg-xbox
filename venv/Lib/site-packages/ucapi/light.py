"""
Light entity definitions.

:copyright: (c) 2023 by Unfolded Circle ApS.
:license: MPL-2.0, see LICENSE for more details.
"""

from enum import Enum
from typing import Any

from ucapi.api_definitions import CommandHandler
from ucapi.entity import Entity, EntityTypes


class States(str, Enum):
    """Light entity states."""

    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"
    ON = "ON"
    OFF = "OFF"


class Features(str, Enum):
    """Light entity features."""

    ON_OFF = "on_off"
    TOGGLE = "toggle"
    DIM = "dim"
    COLOR = "color"
    COLOR_TEMPERATURE = "color_temperature"


class Attributes(str, Enum):
    """Light entity attributes."""

    STATE = "state"
    HUE = "hue"
    SATURATION = "saturation"
    BRIGHTNESS = "brightness"
    COLOR_TEMPERATURE = "color_temperature"


class Commands(str, Enum):
    """Light entity commands."""

    ON = "on"
    OFF = "off"
    TOGGLE = "toggle"


class DeviceClasses(str, Enum):
    """Light entity device classes."""


class Options(str, Enum):
    """Light entity options."""

    COLOR_TEMPERATURE_STEPS = "color_temperature_steps"


class Light(Entity):
    """
    Switch entity class.

    See https://github.com/unfoldedcircle/core-api/blob/main/doc/entities/entity_light.md
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
        cmd_handler: CommandHandler = None,
    ):
        """
        Create light-entity instance.

        :param identifier: entity identifier
        :param name: friendly name
        :param features: light features
        :param attributes: light attributes
        :param device_class: optional light device class
        :param options: options
        :param area: optional area
        :param cmd_handler: handler for entity commands
        """
        super().__init__(
            identifier,
            name,
            EntityTypes.LIGHT,
            features,
            attributes,
            device_class,
            options,
            area,
            cmd_handler,
        )
