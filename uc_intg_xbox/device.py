"""
Xbox device implementation using PollingDevice.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi_framework import DeviceEvents, PollingDevice

from uc_intg_xbox.client import XboxClient
from uc_intg_xbox.config import XboxConfig
from uc_intg_xbox.const import MAX_CONSECUTIVE_FAILURES, POLL_INTERVAL, POLL_INTERVAL_OFF, RECONNECT_INTERVAL

_LOG = logging.getLogger(__name__)


class XboxDevice(PollingDevice):
    """Xbox console device."""

    def __init__(self, device_config: XboxConfig, **kwargs: Any) -> None:
        super().__init__(device_config, poll_interval=POLL_INTERVAL, **kwargs)
        self._device_config = device_config
        self._client: XboxClient | None = None
        self._state: str = "UNAVAILABLE"
        self._consecutive_failures: int = 0
        self._reconnect_poll_count: int = 0

        self._presence_state: str = "OFF"
        self._media_title: str = "Offline"
        self._media_image: str = ""
        self._gamertag: str = "Xbox User"
        self._installed_games: list[dict] = []

    @property
    def identifier(self) -> str:
        return self._device_config.identifier

    @property
    def name(self) -> str:
        return self._device_config.name

    @property
    def address(self) -> str:
        return self._device_config.liveid

    @property
    def log_id(self) -> str:
        return f"{self.name} ({self._device_config.liveid})"

    @property
    def state(self) -> str:
        return self._state

    @property
    def presence_state(self) -> str:
        return self._presence_state

    @property
    def media_title(self) -> str:
        return self._media_title

    @property
    def media_image(self) -> str:
        return self._media_image

    @property
    def gamertag(self) -> str:
        return self._gamertag

    @property
    def installed_games(self) -> list[dict]:
        return self._installed_games

    @property
    def client(self) -> XboxClient | None:
        return self._client

    async def establish_connection(self) -> XboxClient:
        self._client = XboxClient(self._device_config.client_id, self._device_config.client_secret)

        refreshed_tokens = await self._client.connect(self._device_config.tokens)
        if not refreshed_tokens:
            raise ConnectionError(f"Failed to authenticate Xbox client for {self.log_id}")

        self._persist_tokens(refreshed_tokens)
        self._gamertag = self._client.gamertag

        try:
            await self._update_state()
        except ConnectionError:
            _LOG.warning("[%s] Initial state query failed, using defaults", self.log_id)

        try:
            self._installed_games = await self._client.get_installed_apps(self._device_config.liveid)
            _LOG.info("[%s] Found %d installed games", self.log_id, len(self._installed_games))
        except Exception as err:
            _LOG.warning("[%s] Could not fetch game library: %s", self.log_id, err)

        self._state = "ON"
        self._consecutive_failures = 0
        self.push_update()
        return self._client

    async def poll_device(self) -> None:
        if self._state == "UNAVAILABLE":
            self._reconnect_poll_count += 1
            polls_needed = RECONNECT_INTERVAL // max(POLL_INTERVAL, 1)
            if self._reconnect_poll_count >= max(polls_needed, 3):
                self._reconnect_poll_count = 0
                await self._try_reconnect()
            return

        if not self._client:
            return

        try:
            await self._update_state()
            self._consecutive_failures = 0

            if self._presence_state == "OFF":
                self._poll_interval = POLL_INTERVAL_OFF
            else:
                self._poll_interval = POLL_INTERVAL

            self.push_update()
        except Exception as err:
            self._consecutive_failures += 1
            _LOG.debug("[%s] Poll error (%d/%d): %s", self.log_id,
                       self._consecutive_failures, MAX_CONSECUTIVE_FAILURES, err)
            if self._consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                _LOG.warning("[%s] Max failures reached, marking unavailable", self.log_id)
                self._state = "UNAVAILABLE"
                self._presence_state = "OFF"
                self._media_title = "Offline"
                self._media_image = ""
                self._reconnect_poll_count = 0
                self.push_update()
                self.events.emit(DeviceEvents.DISCONNECTED, self.identifier)

    async def _update_state(self) -> None:
        presence = await self._client.get_presence(self._device_config.liveid)
        if not presence:
            if self._presence_state == "OFF" or self._media_title == "Offline":
                raise ConnectionError("Failed to get presence data")
            _LOG.debug("[%s] Presence API returned None, keeping last-known state", self.log_id)
            return

        self._presence_state = presence["state"]
        self._media_title = presence.get("title", "Unknown")
        self._media_image = presence.get("image", "")

    async def _try_reconnect(self) -> bool:
        _LOG.info("[%s] Attempting reconnection...", self.log_id)
        try:
            await self.establish_connection()
            _LOG.info("[%s] Reconnected successfully", self.log_id)
            self.push_update()
            self.events.emit(DeviceEvents.CONNECTED, self.identifier)
            return True
        except Exception as err:
            _LOG.debug("[%s] Reconnection failed: %s", self.log_id, err)
            return False

    async def disconnect(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None
        self._state = "UNAVAILABLE"
        await super().disconnect()

    def _persist_tokens(self, tokens: dict) -> None:
        self.update_config(tokens=tokens)

    async def send_command(self, command: str) -> bool:
        if not self._client or not self._client.is_connected:
            return False
        liveid = self._device_config.liveid
        try:
            match command:
                case "POWER_ON":
                    await self._client.turn_on(liveid)
                case "POWER_OFF":
                    await self._client.turn_off(liveid)
                case "POWER_TOGGLE":
                    if self._presence_state == "OFF":
                        await self._client.turn_on(liveid)
                    else:
                        await self._client.turn_off(liveid)
                case "HOME":
                    await self._client.show_guide(liveid)
                case "BACK":
                    await self._client.go_back(liveid)
                case "MENU":
                    await self._client.press_button(liveid, "Menu")
                case "CONTEXT_MENU":
                    await self._client.press_button(liveid, "View")
                case "DPAD_UP":
                    await self._client.press_button(liveid, "Up")
                case "DPAD_DOWN":
                    await self._client.press_button(liveid, "Down")
                case "DPAD_LEFT":
                    await self._client.press_button(liveid, "Left")
                case "DPAD_RIGHT":
                    await self._client.press_button(liveid, "Right")
                case "DPAD_CENTER" | "OK":
                    await self._client.press_button(liveid, "A")
                case "A":
                    await self._client.press_button(liveid, "A")
                case "B":
                    await self._client.press_button(liveid, "B")
                case "X":
                    await self._client.press_button(liveid, "X")
                case "Y":
                    await self._client.press_button(liveid, "Y")
                case "PLAY":
                    await self._client.play(liveid)
                case "PAUSE":
                    await self._client.pause(liveid)
                case "PLAY_PAUSE":
                    await self._client.play(liveid)
                case "NEXT" | "FAST_FORWARD":
                    await self._client.next_track(liveid)
                case "PREVIOUS" | "REWIND":
                    await self._client.previous_track(liveid)
                case "VOLUME_UP":
                    await self._client.change_volume(liveid, "Up")
                case "VOLUME_DOWN":
                    await self._client.change_volume(liveid, "Down")
                case "MUTE_TOGGLE":
                    await self._client.mute(liveid)
                case "NEXUS":
                    await self._client.press_button(liveid, "Nexus")
                case _:
                    _LOG.warning("[%s] Unknown command: %s", self.log_id, command)
                    return False
            return True
        except Exception as err:
            _LOG.error("[%s] Command %s failed: %s", self.log_id, command, err)
            return False

    async def power_on(self) -> None:
        await self._client.turn_on(self._device_config.liveid)

    async def power_off(self) -> None:
        await self._client.turn_off(self._device_config.liveid)

    async def launch_app(self, one_store_product_id: str) -> None:
        await self._client.launch_app(self._device_config.liveid, one_store_product_id)

    async def refresh_game_library(self) -> None:
        if self._client and self._client.is_connected:
            self._installed_games = await self._client.get_installed_apps(self._device_config.liveid)

    async def refresh_tokens(self) -> None:
        if not self._client:
            return
        refreshed = await self._client.refresh_tokens()
        if refreshed:
            self._persist_tokens(refreshed)
            _LOG.info("[%s] Tokens refreshed and persisted", self.log_id)
