"""
Entity definitions.

:copyright: (c) 2023 by Unfolded Circle ApS.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from enum import Enum
from typing import Any

from ucapi.api_definitions import CommandHandler, StatusCodes

_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)


class EntityTypes(str, Enum):
    """Entity types."""

    COVER = "cover"
    BUTTON = "button"
    CLIMATE = "climate"
    LIGHT = "light"
    MEDIA_PLAYER = "media_player"
    REMOTE = "remote"
    SENSOR = "sensor"
    SWITCH = "switch"


class Entity:
    """
    Entity base class.

    See https://github.com/unfoldedcircle/core-api/blob/main/doc/entities/
    for more information.
    """

    # pylint: disable=R0917
    def __init__(
        self,
        identifier: str,
        name: str | dict[str, str],
        entity_type: EntityTypes,
        features: list[str],
        attributes: dict[str, Any],
        device_class: str | None = None,
        options: dict[str, Any] | None = None,
        area: str | None = None,
        cmd_handler: CommandHandler = None,
    ):
        """
        Initialize entity.

        :param identifier: entity identifier
        :param name: friendly name, either a string or a language dictionary
        :param entity_type: entity type
        :param features: entity feature array
        :param attributes: entity attributes
        :param device_class: entity device class
        :param options: entity options
        :param area: optional area name
        """
        self.id = identifier
        self.name = {"en": name} if isinstance(name, str) else name
        self.entity_type = entity_type
        self.device_id = None
        self.features = features
        self.attributes = attributes
        self.device_class = device_class
        self.options = options
        self.area = area
        self._cmd_handler = cmd_handler

        _LOG.debug("Created %s entity: %s", self.entity_type.value, self.id)

    async def command(
        self, cmd_id: str, params: dict[str, Any] | None = None
    ) -> StatusCodes:
        """
        Execute entity command with the installed command handler.

        Returns NOT_IMPLEMENTED if no command handler is installed.

        :param cmd_id: the command
        :param params: optional command parameters
        :return: command status code to acknowledge to UCR2
        """
        if self._cmd_handler:
            return await self._cmd_handler(self, cmd_id, params)

        _LOG.warning(
            "No command handler for %s: cannot execute command '%s' %s",
            self.id,
            cmd_id,
            params if params else "",
        )
        return StatusCodes.NOT_IMPLEMENTED
