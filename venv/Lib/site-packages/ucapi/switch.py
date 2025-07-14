"""
Switch entity definitions.

:copyright: (c) 2023 by Unfolded Circle ApS.
:license: MPL-2.0, see LICENSE for more details.
"""

from enum import Enum
from typing import Any

from ucapi.api_definitions import CommandHandler
from ucapi.entity import Entity, EntityTypes


class States(str, Enum):
    """Switch entity states."""

    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"
    ON = "ON"
    OFF = "OFF"


class Features(str, Enum):
    """Switch entity features."""

    ON_OFF = "on_off"
    TOGGLE = "toggle"


class Attributes(str, Enum):
    """Switch entity attributes."""

    STATE = "state"


class Commands(str, Enum):
    """Switch entity commands."""

    ON = "on"
    OFF = "off"
    TOGGLE = "toggle"


class DeviceClasses(str, Enum):
    """Switch entity device classes."""

    OUTLET = "outlet"
    SWITCH = "switch"


class Options(str, Enum):
    """Switch entity options."""

    READABLE = "readable"


class Switch(Entity):
    """
    Switch entity class.

    See https://github.com/unfoldedcircle/core-api/blob/main/doc/entities/entity_switch.md
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
        Create switch-entity instance.

        :param identifier: entity identifier
        :param name: friendly name
        :param features: switch features
        :param attributes: switch attributes
        :param device_class: optional switch device class
        :param options: options
        :param area: optional area
        :param cmd_handler: handler for entity commands
        """
        super().__init__(
            identifier,
            name,
            EntityTypes.SWITCH,
            features,
            attributes,
            device_class,
            options,
            area,
            cmd_handler,
        )
