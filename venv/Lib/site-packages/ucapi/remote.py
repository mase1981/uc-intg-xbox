"""
Remote entity definitions.

:copyright: (c) 2024 by Unfolded Circle ApS.
:license: MPL-2.0, see LICENSE for more details.
"""

import dataclasses
from enum import Enum
from typing import Any

from ucapi.api_definitions import CommandHandler
from ucapi.entity import Entity, EntityTypes
from ucapi.ui import DeviceButtonMapping, EntityCommand, UiPage


class States(str, Enum):
    """Remote entity states."""

    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"
    ON = "ON"
    OFF = "OFF"


class Features(str, Enum):
    """Remote entity features."""

    ON_OFF = "on_off"
    TOGGLE = "toggle"
    SEND_CMD = "send_cmd"


class Attributes(str, Enum):
    """Remote entity attributes."""

    STATE = "state"


class Commands(str, Enum):
    """Remote entity commands."""

    ON = "on"
    OFF = "off"
    TOGGLE = "toggle"
    SEND_CMD = "send_cmd"
    SEND_CMD_SEQUENCE = "send_cmd_sequence"


class Options(str, Enum):
    """Remote entity options."""

    SIMPLE_COMMANDS = "simple_commands"
    BUTTON_MAPPING = "button_mapping"
    USER_INTERFACE = "user_interface"


def create_send_cmd(
    command: str,
    delay: int | None = None,
    repeat: int | None = None,
    hold: int | None = None,
) -> EntityCommand:
    """
    Create a remote send command.

    :param command: command to send.
    :param delay: optional delay in milliseconds after the command or between repeats.
    :param repeat: optional repeat count of the command.
    :param hold: optional hold time in milliseconds.
    :return: the created EntityCommand.
    """
    params = {"command": command}
    if delay:
        params["delay"] = delay
    if repeat:
        params["repeat"] = repeat
    if hold:
        params["hold"] = hold
    return EntityCommand(Commands.SEND_CMD.value, params)


def create_sequence_cmd(
    sequence: list[str],
    delay: int | None = None,
    repeat: int | None = None,
) -> EntityCommand:
    """
    Create a remote send sequence command.

    :param sequence: list of simple commands.
    :param delay: optional delay in milliseconds between the commands in the sequence.
    :param repeat: optional repeat count of the sequence.
    :return: the created EntityCommand.
    """
    params = {"sequence": sequence}
    if delay:
        params["delay"] = delay
    if repeat:
        params["repeat"] = repeat
    return EntityCommand(Commands.SEND_CMD_SEQUENCE.value, params)


def _list_items_asdict(obj: list[Any]):
    """Convert a list with (mixed) dataclass items to dictionary mapping items."""
    return list(
        map(
            lambda item: (
                dataclasses.asdict(item) if dataclasses.is_dataclass(item) else item
            ),
            obj,
        )
    )


class Remote(Entity):
    """
    Remote entity class.

    See https://github.com/unfoldedcircle/core-api/blob/main/doc/entities/entity_remote.md
    for more information.
    """

    # pylint: disable=R0917
    def __init__(
        self,
        identifier: str,
        name: str | dict[str, str],
        features: list[Features],
        attributes: dict[str, Any],
        simple_commands: list[str] | None = None,
        button_mapping: list[DeviceButtonMapping | dict[str, Any]] | None = None,
        ui_pages: list[UiPage | dict[str, Any]] | None = None,
        area: str | None = None,
        cmd_handler: CommandHandler = None,
    ):
        """
        Create remote entity instance.

        :param identifier: entity identifier
        :param name: friendly name
        :param features: remote features
        :param attributes: remote attributes
        :param simple_commands: optional list of supported remote command identifiers
        :param button_mapping: optional command mapping of physical buttons
               Either with DeviceButtonMapping items or plain dictionary items.
        :param ui_pages: optional user interface page definitions.
               Either with UiPage items or plain dictionary items.
        :param area: optional area
        :param cmd_handler: handler for entity commands
        """
        options: dict[str, Any] = {}
        if simple_commands:
            options["simple_commands"] = simple_commands
        if button_mapping:
            options["button_mapping"] = _list_items_asdict(button_mapping)
        if ui_pages:
            options["user_interface"] = {"pages": _list_items_asdict(ui_pages)}
        super().__init__(
            identifier,
            name,
            EntityTypes.REMOTE,
            features,
            attributes,
            options=options,
            area=area,
            cmd_handler=cmd_handler,
        )
