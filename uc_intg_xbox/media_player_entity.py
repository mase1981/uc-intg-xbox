"""
Xbox media player entity.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import Pagination, StatusCodes, media_player
from ucapi.api_definitions import Paging
from ucapi.media_player import (
    BrowseMediaItem,
    BrowseOptions,
    BrowseResults,
    MediaClass,
    MediaContentType,
    SearchOptions,
    SearchResults,
)
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
    media_player.Features.BROWSE_MEDIA,
    media_player.Features.SEARCH_MEDIA,
    media_player.Features.PLAY_MEDIA,
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
            self.set_state(media_player.States.UNAVAILABLE, update=True)
            return

        presence = self._device.presence_state
        if presence == "OFF":
            state = media_player.States.OFF
        elif presence == "PLAYING":
            state = media_player.States.PLAYING
        else:
            state = media_player.States.ON

        self.set_attributes(
            state=state,
            media_title=self._device.media_title or "",
            media_image_url=self._device.media_image or "",
            media_type=MediaContentType.GAME if presence == "PLAYING" else "",
            update=True,
        )

    async def browse(self, options: BrowseOptions) -> BrowseResults | StatusCodes:
        if not self._device.client or not self._device.client.is_connected:
            return StatusCodes.SERVICE_UNAVAILABLE

        if self._device.state == "UNAVAILABLE":
            return StatusCodes.SERVICE_UNAVAILABLE

        try:
            await self._device.refresh_game_library()
        except Exception as err:
            _LOG.warning("[%s] Could not refresh game library: %s", self.id, err)

        games = self._device.installed_games
        paging: Paging = options.paging

        page_games = games[paging.offset : paging.offset + paging.limit]

        items = [
            BrowseMediaItem(
                media_id=game["one_store_product_id"],
                title=game["name"],
                media_class=MediaClass.GAME,
                can_browse=False,
                can_play=True,
                thumbnail=game.get("image") or None,
            )
            for game in page_games
        ]

        return BrowseResults(
            media=BrowseMediaItem(
                media_id="xbox_games",
                title="Games",
                media_class=MediaClass.GAME,
                can_browse=True,
                items=items,
            ),
            pagination=Pagination(
                page=paging.page,
                limit=len(items),
                count=len(games),
            ),
        )

    async def search(self, options: SearchOptions) -> SearchResults | StatusCodes:
        if not self._device.client or not self._device.client.is_connected:
            return StatusCodes.SERVICE_UNAVAILABLE

        query = options.query.lower() if options.query else ""
        if not query:
            return SearchResults(media=[], pagination=Pagination(page=1, limit=0, count=0))

        matches = [
            BrowseMediaItem(
                media_id=game["one_store_product_id"],
                title=game["name"],
                media_class=MediaClass.GAME,
                can_browse=False,
                can_play=True,
                thumbnail=game.get("image") or None,
            )
            for game in self._device.installed_games
            if query in game["name"].lower()
        ]

        paging: Paging = options.paging
        page_matches = matches[paging.offset : paging.offset + paging.limit]

        return SearchResults(
            media=page_matches,
            pagination=Pagination(
                page=paging.page,
                limit=len(page_matches),
                count=len(matches),
            ),
        )

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
                case media_player.Commands.PLAY_MEDIA:
                    return await self._handle_play_media(params)
                case _:
                    return StatusCodes.NOT_IMPLEMENTED
            return StatusCodes.OK
        except Exception as err:
            _LOG.error("[%s] Command %s failed: %s", entity.id, cmd_id, err)
            return StatusCodes.SERVER_ERROR

    async def _handle_play_media(self, params: dict[str, Any] | None) -> StatusCodes:
        if not params:
            return StatusCodes.BAD_REQUEST
        media_id = params.get("media_id", "")
        if not media_id:
            return StatusCodes.BAD_REQUEST

        await self._device.launch_app(media_id)
        return StatusCodes.OK
