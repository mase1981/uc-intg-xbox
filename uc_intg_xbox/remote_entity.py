"""
Xbox remote entity with UI pages and button mappings.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes, remote
from ucapi.ui import Buttons, Size, UiPage, create_btn_mapping, create_ui_icon, create_ui_text
from ucapi_framework import RemoteEntity

from uc_intg_xbox.config import XboxConfig
from uc_intg_xbox.device import XboxDevice

_LOG = logging.getLogger(__name__)

SIMPLE_COMMANDS = [
    "POWER_ON", "POWER_OFF", "POWER_TOGGLE",
    "DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT", "DPAD_CENTER",
    "A", "B", "X", "Y",
    "BACK", "HOME", "MENU", "CONTEXT_MENU", "NEXUS",
    "PLAY", "PAUSE", "PLAY_PAUSE", "NEXT", "PREVIOUS", "FAST_FORWARD", "REWIND",
    "VOLUME_UP", "VOLUME_DOWN", "MUTE_TOGGLE",
]


def _create_button_mapping() -> list:
    return [
        create_btn_mapping(Buttons.HOME, short="HOME"),
        create_btn_mapping(Buttons.BACK, short="BACK"),
        create_btn_mapping(Buttons.DPAD_UP, short="DPAD_UP"),
        create_btn_mapping(Buttons.DPAD_DOWN, short="DPAD_DOWN"),
        create_btn_mapping(Buttons.DPAD_LEFT, short="DPAD_LEFT"),
        create_btn_mapping(Buttons.DPAD_RIGHT, short="DPAD_RIGHT"),
        create_btn_mapping(Buttons.DPAD_MIDDLE, short="A"),
        create_btn_mapping(Buttons.VOLUME_UP, short="VOLUME_UP"),
        create_btn_mapping(Buttons.VOLUME_DOWN, short="VOLUME_DOWN"),
        create_btn_mapping(Buttons.MUTE, short="MUTE_TOGGLE"),
        create_btn_mapping(Buttons.MENU, short="MENU"),
        create_btn_mapping(Buttons.PLAY, short="PLAY_PAUSE"),
        create_btn_mapping(Buttons.PREV, short="PREVIOUS"),
        create_btn_mapping(Buttons.NEXT, short="NEXT"),
        create_btn_mapping(Buttons.POWER, short="POWER_TOGGLE"),
        create_btn_mapping(Buttons.GREEN, short="A"),
        create_btn_mapping(Buttons.RED, short="B"),
        create_btn_mapping(Buttons.YELLOW, short="Y"),
        create_btn_mapping(Buttons.BLUE, short="X"),
    ]


def _create_ui_pages() -> list[UiPage]:
    main_page = UiPage("main", "Main", grid=Size(4, 6), items=[
        create_ui_icon("uc:power-on", 0, 0, cmd="POWER_TOGGLE"),
        create_ui_text("Guide", 1, 0, cmd="HOME"),
        create_ui_text("Menu", 2, 0, cmd="MENU"),
        create_ui_text("Nexus", 3, 0, cmd="NEXUS"),
        create_ui_icon("uc:up-arrow", 1, 1, cmd="DPAD_UP"),
        create_ui_icon("uc:left-arrow", 0, 2, cmd="DPAD_LEFT"),
        create_ui_text("OK", 1, 2, cmd="A"),
        create_ui_icon("uc:right-arrow", 2, 2, cmd="DPAD_RIGHT"),
        create_ui_icon("uc:down-arrow", 1, 3, cmd="DPAD_DOWN"),
        create_ui_text("Back", 3, 2, cmd="BACK"),
    ])

    buttons_page = UiPage("buttons", "Xbox Buttons", grid=Size(4, 6), items=[
        create_ui_text("Y", 1, 0, cmd="Y"),
        create_ui_text("X", 0, 1, cmd="X"),
        create_ui_text("B", 2, 1, cmd="B"),
        create_ui_text("A", 1, 2, cmd="A"),
        create_ui_text("View", 0, 3, cmd="CONTEXT_MENU"),
        create_ui_text("Menu", 2, 3, cmd="MENU"),
    ])

    media_page = UiPage("media", "Media", grid=Size(4, 6), items=[
        create_ui_icon("uc:prev", 0, 0, cmd="PREVIOUS"),
        create_ui_icon("uc:play", 1, 0, cmd="PLAY"),
        create_ui_icon("uc:pause", 2, 0, cmd="PAUSE"),
        create_ui_icon("uc:next", 3, 0, cmd="NEXT"),
        create_ui_icon("uc:bw", 0, 1, cmd="REWIND"),
        create_ui_icon("uc:ff", 3, 1, cmd="FAST_FORWARD"),
        create_ui_icon("uc:vol-up", 0, 2, cmd="VOLUME_UP"),
        create_ui_icon("uc:vol-down", 0, 3, cmd="VOLUME_DOWN"),
        create_ui_icon("uc:mute", 1, 3, cmd="MUTE_TOGGLE"),
    ])

    return [main_page, buttons_page, media_page]


class XboxRemote(RemoteEntity):
    """Xbox remote entity."""

    def __init__(self, device_config: XboxConfig, device: XboxDevice) -> None:
        self._device = device
        entity_id = f"remote.{device_config.identifier}"
        super().__init__(
            entity_id,
            f"{device_config.name} Remote",
            [remote.Features.ON_OFF, remote.Features.TOGGLE, remote.Features.SEND_CMD],
            {remote.Attributes.STATE: remote.States.UNKNOWN},
            simple_commands=SIMPLE_COMMANDS,
            button_mapping=_create_button_mapping(),
            ui_pages=_create_ui_pages(),
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "UNAVAILABLE":
            self.update({remote.Attributes.STATE: remote.States.UNAVAILABLE})
            return
        state = remote.States.OFF if self._device.presence_state == "OFF" else remote.States.ON
        self.update({remote.Attributes.STATE: state})

    async def _handle_command(
        self, entity: Any, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        try:
            if cmd_id == remote.Commands.ON:
                await self._device.power_on()
                return StatusCodes.OK
            if cmd_id == remote.Commands.OFF:
                await self._device.power_off()
                return StatusCodes.OK
            if cmd_id == remote.Commands.TOGGLE:
                await self._device.send_command("POWER_TOGGLE")
                return StatusCodes.OK
            if cmd_id == remote.Commands.SEND_CMD and params:
                command = params.get("command", "")
                if command:
                    success = await self._device.send_command(command)
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            if cmd_id == remote.Commands.SEND_CMD_SEQUENCE and params:
                for command in params.get("sequence", []):
                    success = await self._device.send_command(command)
                    if not success:
                        return StatusCodes.SERVER_ERROR
                return StatusCodes.OK
            return StatusCodes.NOT_IMPLEMENTED
        except Exception as err:
            _LOG.error("[%s] Command %s failed: %s", entity.id, cmd_id, err)
            return StatusCodes.SERVER_ERROR
