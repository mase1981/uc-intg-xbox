"""
Button entity definitions.

:copyright: (c) 2023 by Unfolded Circle ApS.
:license: MPL-2.0, see LICENSE for more details.
"""

from enum import Enum

from ucapi.api_definitions import CommandHandler
from ucapi.entity import Entity, EntityTypes


class States(str, Enum):
    """Button entity states."""

    UNAVAILABLE = "UNAVAILABLE"
    AVAILABLE = "AVAILABLE"


class Attributes(str, Enum):
    """Button entity attributes."""

    STATE = "state"


class Commands(str, Enum):
    """Button entity commands."""

    PUSH = "push"


class Button(Entity):
    """
    Button entity class.

    See https://github.com/unfoldedcircle/core-api/blob/main/doc/entities/entity_button.md
    for more information.
    """  # noqa

    def __init__(
        self,
        identifier: str,
        name: str | dict[str, str],
        area: str | None = None,
        cmd_handler: CommandHandler = None,
    ):
        """
        Create button-entity instance.

        :param identifier: entity identifier
        :param name: friendly name, either a string or a language dictionary
        :param area: optional area name
        :param cmd_handler: handler for entity commands
        """
        super().__init__(
            identifier,
            name,
            EntityTypes.BUTTON,
            ["press"],
            {Attributes.STATE: States.AVAILABLE},
            area=area,
            cmd_handler=cmd_handler,
        )
