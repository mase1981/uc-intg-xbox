"""
User interface definitions.

:copyright: (c) 2024 by Unfolded Circle ApS.
:license: MPL-2.0, see LICENSE for more details.
"""

from dataclasses import KW_ONLY, dataclass
from enum import Enum


@dataclass
class EntityCommand:
    """Remote command definition for a button mapping or UI page definition."""

    cmd_id: str
    params: dict[str, str | int | list[str]] | None = None


class Buttons(str, Enum):
    """Physical buttons."""

    BACK = "BACK"
    HOME = "HOME"
    VOICE = "VOICE"
    VOLUME_UP = "VOLUME_UP"
    VOLUME_DOWN = "VOLUME_DOWN"
    MUTE = "MUTE"
    DPAD_UP = "DPAD_UP"
    DPAD_DOWN = "DPAD_DOWN"
    DPAD_LEFT = "DPAD_LEFT"
    DPAD_RIGHT = "DPAD_RIGHT"
    DPAD_MIDDLE = "DPAD_MIDDLE"
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"
    BLUE = "BLUE"
    CHANNEL_UP = "CHANNEL_UP"
    CHANNEL_DOWN = "CHANNEL_DOWN"
    PREV = "PREV"
    PLAY = "PLAY"
    NEXT = "NEXT"
    POWER = "POWER"


@dataclass
class DeviceButtonMapping:
    """Physical button command mapping."""

    button: str
    """Physical button identifier. See Buttons for Remote Two identifiers."""
    short_press: EntityCommand | None = None
    """Short press command of the button."""
    long_press: EntityCommand | None = None
    """Long press command of the button."""


def create_btn_mapping(
    button: Buttons,
    short: str | EntityCommand | None = None,
    long: str | EntityCommand | None = None,
) -> DeviceButtonMapping:
    """
    Create a physical button command mapping.

    :param button: physical button identifier.
    :param short: associated short-press command to the physical button.
                  A string parameter corresponds to a simple command, whereas an
                  ``EntityCommand`` allows to customize the command.
    :param long: associated long-press command to the physical button
    :return: the created DeviceButtonMapping
    """
    if isinstance(short, str):
        short = EntityCommand(short)
    if isinstance(long, str):
        long = EntityCommand(long)
    return DeviceButtonMapping(button.value, short_press=short, long_press=long)


@dataclass
class Size:
    """Item size in the button grid. Default size if not specified: 1x1."""

    width: int = 1
    height: int = 1


@dataclass
class Location:
    """Button placement in the grid with 0-based coordinates."""

    x: int
    y: int


@dataclass
class UiItem:
    """
    A user interface item is either an icon or text.

    - Icon and text items can be static or linked to a command specified in the
      `command` field.
    - Default size is 1x1 if not specified.
    """

    type: str
    location: Location
    size: Size | None = None
    icon: str | None = None
    text: str | None = None
    command: EntityCommand | None = None


def create_ui_text(
    text: str,
    x: int,
    y: int,
    size: Size | None = None,
    cmd: str | EntityCommand | None = None,
) -> UiItem:
    """
    Create a text UI item.

    :param text: the text to show in the UI item.
    :param x: x-position, 0-based.
    :param y: y-position, 0-based.
    :param size: item size, defaults to 1 x 1 if not specified.
    :param cmd: associated command to the text item. A string parameter corresponds to
                a simple command, whereas an ``EntityCommand`` allows to customize the
                command for example with number of repeats.
    :return: the created UiItem
    """
    if isinstance(cmd, str):
        cmd = EntityCommand(cmd)
    return UiItem("text", Location(x, y), size=size, text=text, command=cmd)


def create_ui_icon(
    icon: str,
    x: int,
    y: int,
    size: Size | None = None,
    cmd: str | EntityCommand | None = None,
) -> UiItem:
    """
    Create an icon UI item.

    The icon identifier consists of a prefix and a resource identifier,
    separated by `:`. Available prefixes:
      - `uc:` - integrated icon font
      - `custom:` - custom resource

    :param icon: the icon identifier of the icon to show in the UI item.
    :param x: x-position, 0-based.
    :param y: y-position, 0-based.
    :param size: item size, defaults to 1 x 1 if not specified.
    :param cmd: associated command to the text item. A string parameter corresponds to
                a simple command, whereas an ``EntityCommand`` allows to customize the
                command for example with number of repeats.
    :return: the created UiItem
    """
    if isinstance(cmd, str):
        cmd = EntityCommand(cmd)
    return UiItem("icon", Location(x, y), size=size, icon=icon, command=cmd)


@dataclass
class UiPage:
    """
    Definition of a complete user interface page.

    Default grid size is 4x6 if not specified.
    """

    page_id: str
    name: str
    _: KW_ONLY
    grid: Size = None
    items: list[UiItem] = None

    def __post_init__(self):
        """Post initialization to set required fields."""
        # grid and items are required Integration-API fields
        if self.grid is None:
            self.grid = Size(4, 6)
        if self.items is None:
            self.items = []

    def add(self, item: UiItem):
        """Append the given UiItem to the page items."""
        self.items.append(item)
