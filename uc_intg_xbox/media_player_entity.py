"""
Xbox media player entity.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes, media_player
from ucapi_framework import MediaPlayerEntity

from uc_intg_xbox.config import XboxConfig
from uc_intg_xbox.device import XboxDevice

_LOG = logging.getLogger(__name__)

FEATURES = [
    media_player.Features.ON_OFF,
    media_player.Features.TOGGLE,
    media_player.Features.PLAY_PAUSE,
    media_player.Features.NEXT,
    media_player.Features.PREVIOUS,
    media_player.Features.FAST_FORWARD,
    media_player.Features.REWIND,
    media_player.Features.VOLUME_UP_DOWN,
    media_player.Features.MUTE_TOGGLE,
    media_player.Features.MEDIA_TITLE,
    media_player.Features.MEDIA_IMAGE_URL,
    media_player.Features.MEDIA_TYPE,
    media_player.Features.HOME,
    media_player.Features.MENU,
    media_player.Features.CONTEXT_MENU,
    media_player.Features.DPAD,
    media_player.Features.COLOR_BUTTONS,
]


class XboxMediaPlayer(MediaPlayerEntity):
    """Xbox media player entity."""

    def __init__(self, device_config: XboxConfig, device: XboxDevice) -> None:
        self._device = device
        entity_id = f"media_player.{device_config.identifier}"
        super().__init__(
            entity_id,
            device_config.name,
            FEATURES,
            {
                media_player.Attributes.STATE: media_player.States.UNKNOWN,
                media_player.Attributes.MEDIA_TITLE: "",
                media_player.Attributes.MEDIA_IMAGE_URL: "",
                media_player.Attributes.MEDIA_TYPE: "",
            },
            device_class=media_player.DeviceClasses.SET_TOP_BOX,
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "UNAVAILABLE":
            self.update({media_player.Attributes.STATE: media_player.States.UNAVAILABLE})
            return

        presence = self._device.presence_state
        if presence == "OFF":
            state = media_player.States.OFF
        elif presence == "PLAYING":
            state = media_player.States.PLAYING
        else:
            state = media_player.States.ON

        self.update({
            media_player.Attributes.STATE: state,
            media_player.Attributes.MEDIA_TITLE: self._device.media_title or "",
            media_player.Attributes.MEDIA_IMAGE_URL: self._device.media_image or "",
            media_player.Attributes.MEDIA_TYPE: "game" if presence == "PLAYING" else "",
        })

    async def _handle_command(
        self, entity: Any, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        try:
            match cmd_id:
                case media_player.Commands.ON:
                    await self._device.power_on()
                case media_player.Commands.OFF:
                    await self._device.power_off()
                case media_player.Commands.TOGGLE:
                    await self._device.send_command("POWER_TOGGLE")
                case media_player.Commands.PLAY_PAUSE:
                    await self._device.send_command("PLAY_PAUSE")
                case media_player.Commands.NEXT:
                    await self._device.send_command("NEXT")
                case media_player.Commands.PREVIOUS:
                    await self._device.send_command("PREVIOUS")
                case media_player.Commands.FAST_FORWARD:
                    await self._device.send_command("FAST_FORWARD")
                case media_player.Commands.REWIND:
                    await self._device.send_command("REWIND")
                case media_player.Commands.VOLUME_UP:
                    await self._device.send_command("VOLUME_UP")
                case media_player.Commands.VOLUME_DOWN:
                    await self._device.send_command("VOLUME_DOWN")
                case media_player.Commands.MUTE_TOGGLE:
                    await self._device.send_command("MUTE_TOGGLE")
                case media_player.Commands.HOME:
                    await self._device.send_command("HOME")
                case media_player.Commands.MENU:
                    await self._device.send_command("MENU")
                case media_player.Commands.CONTEXT_MENU:
                    await self._device.send_command("CONTEXT_MENU")
                case media_player.Commands.CURSOR_UP:
                    await self._device.send_command("DPAD_UP")
                case media_player.Commands.CURSOR_DOWN:
                    await self._device.send_command("DPAD_DOWN")
                case media_player.Commands.CURSOR_LEFT:
                    await self._device.send_command("DPAD_LEFT")
                case media_player.Commands.CURSOR_RIGHT:
                    await self._device.send_command("DPAD_RIGHT")
                case media_player.Commands.CURSOR_ENTER:
                    await self._device.send_command("A")
                case media_player.Commands.BACK:
                    await self._device.send_command("BACK")
                case media_player.Commands.FUNCTION_RED:
                    await self._device.send_command("B")
                case media_player.Commands.FUNCTION_GREEN:
                    await self._device.send_command("A")
                case media_player.Commands.FUNCTION_YELLOW:
                    await self._device.send_command("Y")
                case media_player.Commands.FUNCTION_BLUE:
                    await self._device.send_command("X")
                case _:
                    return StatusCodes.NOT_IMPLEMENTED
            return StatusCodes.OK
        except Exception as err:
            _LOG.error("[%s] Command %s failed: %s", entity.id, cmd_id, err)
            return StatusCodes.SERVER_ERROR
