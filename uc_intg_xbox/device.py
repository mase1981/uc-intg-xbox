"""
Xbox device implementation using PollingDevice.

State comes from the console itself (power, playback and the app in focus),
the same source Home Assistant uses. If that call fails, the account presence
is used as before, so the tile never goes blank. Profile, friends and storage
refresh less often than the console status.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from ucapi_framework import DeviceEvents, PollingDevice

from uc_intg_xbox.client import XboxClient
from uc_intg_xbox.config import XboxConfig
from uc_intg_xbox.const import (
    CONSOLES_EVERY,
    FRIENDS_EVERY,
    MAX_CONSECUTIVE_FAILURES,
    POLL_INTERVAL,
    PROFILE_FAST_EVERY,
    PROFILE_EVERY,
    RECONNECT_INTERVAL,
    RECONNECT_MAX,
)

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
        self._reconnect_wait: int = RECONNECT_INTERVAL  # seconds, doubles on each failure
        self._tick: int = 0
        # The framework can call connect() twice at once; one client per device.
        self._connect_lock = asyncio.Lock()

        # Presence (fallback) state, as before
        self._presence_state: str = "OFF"
        self._last_focus: str | None = None  # app in focus at the previous poll
        self._last_logged: tuple | None = None
        # Set by the Home command: Xbox Live keeps reporting a suspended game as active
        # (Quick Resume), so after going Home the integration shows Home itself until
        # something new starts. Holds what was running when Home was pressed.
        self._home: dict | None = None
        self._media_title: str = "Offline"
        self._media_image: str = ""
        self._gamertag: str = "Xbox User"
        self._installed_games: list[dict] = []
        self._library_task: asyncio.Task | None = None

        # Console status (primary)
        self._console: dict | None = None  # {"power", "playback", "focus_app", "app"}
        self._profile: dict | None = None
        self._progress: dict | None = None
        self._progress_title: str | None = None
        self._friends_online: int | None = None
        self._storage: list[dict] = []

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # State for entities
    # ------------------------------------------------------------------
    @property
    def presence_state(self) -> str:
        """OFF, ON or PLAYING (kept for compatibility)."""
        player = self.player_state
        return "OFF" if player == "OFF" else ("PLAYING" if player in ("PLAYING", "PAUSED") else "ON")

    def _console_app(self) -> dict | None:
        """The app in focus when the Store catalog named it, else None."""
        if self._console is None:
            return None
        app = self._console.get("app") or {}
        return app if app.get("title") else None

    def _activity_signature(self) -> tuple:
        """What presence and the console say is running (to notice that something new started)."""
        profile = self._profile or {}
        focus = (self._console or {}).get("focus_app") or ""
        return (profile.get("title_id"), profile.get("status"), focus)

    def _clear_home(self, reason: str) -> None:
        if self._home is not None:
            _LOG.info("[%s] Leaving Home: %s", self.log_id, reason)
            self._home = None

    def _check_home(self) -> None:
        """Keep showing Home until a different game or app shows up."""
        if self._home is None:
            return
        if self._console is not None and self._console["power"] != "On":
            self._clear_home("console off")
            return
        before, now = self._home["signature"], self._activity_signature()
        if before[:2] == (None, None) and now[:2] != (None, None):
            self._home["signature"] = now  # no profile was known when Home was pressed
            return
        if now[2] and now[2] != before[2]:
            self._clear_home("console reports another app")
        elif now[0] and now[0] != before[0]:
            self._clear_home("presence reports another game")
        elif not now[0] and now[1] not in (before[1], "Home") and now[1]:
            self._clear_home("presence reports another app")

    def _profile_activity(self) -> dict | None:
        """What the profile says is running (the same source as the Status sensor).

        Used when the console reports an app the Store catalog cannot name, or no app
        at all (some consoles leave the focus app empty while a game runs).
        """
        profile = self._profile
        if not profile or not profile.get("online"):
            return None
        title_id = profile.get("title_id")
        if title_id:
            info = self._progress if self._progress_title == title_id else None
            return {
                "title": (info or {}).get("name") or profile.get("status") or "",
                "image": (info or {}).get("image") or "",
                "is_game": True,
            }
        return {"title": profile.get("status") or "", "image": "", "is_game": False}

    @property
    def player_state(self) -> str:
        """OFF, ON, PLAYING or PAUSED."""
        if self._console is not None:
            if self._console["power"] != "On":
                return "OFF"
            if self._console["playback"] == "Playing":
                return "PLAYING"
            if self._console["playback"] == "Paused":
                return "PAUSED"
            if self._home is not None:
                return "ON"
            app = self._console_app() or self._profile_activity()
            return "PLAYING" if app and app.get("is_game") else "ON"
        return self._presence_state

    @property
    def is_game(self) -> bool:
        if self._home is not None:
            return False
        if self._console is not None:
            app = self._console_app() or self._profile_activity()
            return bool(app and app.get("is_game"))
        return self._presence_state == "PLAYING"

    @property
    def media_title(self) -> str:
        if self._console is not None:
            if self._console["power"] != "On":
                return "Offline"
            if self._home is not None:
                return "Home"
            app = self._console_app() or self._profile_activity()
            return app["title"] if app else ""
        return self._media_title

    @property
    def media_image(self) -> str:
        if self._console is not None:
            if self._console["power"] != "On" or self._home is not None:
                return ""
            app = self._console_app() or self._profile_activity()
            return (app or {}).get("image") or ""
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

    @property
    def profile(self) -> dict | None:
        return self._profile

    @property
    def progress(self) -> dict | None:
        return None if self._home is not None else self._progress

    @property
    def friends_online(self) -> int | None:
        return self._friends_online

    @property
    def storage(self) -> list[dict]:
        return self._storage

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------
    async def connect(self) -> bool:
        async with self._connect_lock:
            return await super().connect()

    async def _connect_client(self) -> bool:
        """Sign in with the stored tokens. Never raises."""
        if self._client:
            await self._client.close()  # never leave the previous HTTP session open
            self._client = None
        client = XboxClient(self._device_config.client_id, self._device_config.client_secret)
        try:
            refreshed = await client.connect(self._device_config.tokens, on_tokens_refreshed=self._persist_tokens)
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.warning("[%s] Sign-in failed: %s", self.log_id, err)
            await client.close()
            return False
        if not refreshed:
            await client.close()
            return False
        self._client = client
        self._gamertag = client.gamertag
        return True

    async def establish_connection(self) -> XboxClient | None:
        """Connect; on failure stay UNAVAILABLE and let the poll loop retry (never raise)."""
        if not await self._connect_client():
            self._state = "UNAVAILABLE"
            self._reconnect_poll_count = 0
            self.push_update()
            return None
        self._reconnect_wait = RECONNECT_INTERVAL
        await self._after_connect()
        return self._client

    async def _after_connect(self) -> None:
        self._tick = 0
        try:
            await self._update_state()
        except ConnectionError:
            _LOG.warning("[%s] Initial state query failed, using defaults", self.log_id)
        self._state = "ON"
        self._consecutive_failures = 0
        self.push_update()
        self._schedule_library_refresh()

    def _schedule_library_refresh(self) -> None:
        if self._library_task and not self._library_task.done():
            return
        self._library_task = asyncio.create_task(self._refresh_library())

    async def _refresh_library(self) -> None:
        try:
            self._installed_games = await self._client.get_installed_apps(self._device_config.liveid)
            _LOG.info("[%s] Found %d installed games", self.log_id, len(self._installed_games))
            self.push_update()
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.warning("[%s] Could not fetch game library: %s", self.log_id, err)

    async def poll_device(self) -> None:
        if self._state == "UNAVAILABLE":
            self._reconnect_poll_count += 1
            polls_needed = self._reconnect_wait // max(POLL_INTERVAL, 1)
            if self._reconnect_poll_count >= max(polls_needed, 1):
                self._reconnect_poll_count = 0
                if await self._try_reconnect():
                    self._reconnect_wait = RECONNECT_INTERVAL
                else:
                    # Back off so a revoked sign-in does not hit Microsoft every 30 seconds.
                    self._reconnect_wait = min(self._reconnect_wait * 2, RECONNECT_MAX)
            return

        if not self._client:
            return

        try:
            await self._update_state()
            self._consecutive_failures = 0
            self.push_update()
        except Exception as err:  # pylint: disable=broad-exception-caught
            self._consecutive_failures += 1
            _LOG.debug("[%s] Poll error (%d/%d): %s", self.log_id,
                       self._consecutive_failures, MAX_CONSECUTIVE_FAILURES, err)
            if self._consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                _LOG.warning("[%s] Max failures reached, marking unavailable", self.log_id)
                self._state = "UNAVAILABLE"
                self._presence_state = "OFF"
                self._media_title = "Offline"
                self._media_image = ""
                self._console = None
                self._reconnect_poll_count = 0
                self.push_update()
                self.events.emit(DeviceEvents.DISCONNECTED, self.identifier)

    async def _update_state(self) -> None:
        """Console status every poll; profile, friends and storage less often."""
        liveid = self._device_config.liveid
        tick = self._tick
        self._tick += 1

        console_ok = False
        try:
            self._console = await self._client.get_console_status(liveid)
            console_ok = True
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.debug("[%s] Console status unavailable, using presence: %s", self.log_id, err)
            self._console = None

        focus_changed = False
        profile_every = PROFILE_EVERY
        if not console_ok:
            await self._update_presence()
        elif self._console["power"] == "On":
            focus = self._console.get("focus_app") or ""
            if focus != self._last_focus:
                focus_changed = self._last_focus is not None
                self._last_focus = focus
            if self._console_app() is None:
                # Title comes from the profile: refresh it more often while it is needed.
                profile_every = PROFILE_FAST_EVERY
        self._log_console_change()

        if tick % profile_every == 0 or focus_changed:  # follow a game change sooner
            await self._update_profile()
        self._check_home()
        if tick % FRIENDS_EVERY == 0:
            await self._quietly(self._update_friends())
        if tick % CONSOLES_EVERY == 0:
            await self._quietly(self._update_storage())

    def _log_console_change(self) -> None:
        """Log what the console reports when it changes (to diagnose title problems)."""
        console = self._console
        snapshot = None if console is None else (
            console["power"], console["playback"], console.get("focus_app") or "",
            (console.get("app") or {}).get("title") or "",
        )
        if snapshot != self._last_logged:
            self._last_logged = snapshot
            if snapshot is not None:
                _LOG.info("[%s] Console: power=%s playback=%s focus=%r catalog_title=%r",
                          self.log_id, *snapshot)

    async def _update_presence(self) -> None:
        """The previous (presence based) state source, used when console status fails."""
        presence = await self._client.get_presence(self._device_config.liveid)
        if not presence:
            if self._presence_state == "OFF" or self._media_title == "Offline":
                raise ConnectionError("Failed to get presence data")
            _LOG.debug("[%s] Presence API returned None, keeping last-known state", self.log_id)
            return
        self._presence_state = presence["state"]
        self._media_title = presence.get("title", "Unknown")
        self._media_image = presence.get("image", "")

    async def _update_profile(self) -> None:
        try:
            profile = await self._client.get_profile()
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.debug("[%s] Profile unavailable: %s", self.log_id, err)
            return
        if profile is None:
            return
        previous = (self._profile or {}).get("last_seen")
        if previous and profile.get("last_seen") and isinstance(previous, datetime):
            # The API flips between two close timestamps; keep the newest (as Home Assistant does).
            profile["last_seen"] = max(previous, profile["last_seen"])
        self._profile = profile
        title_id = profile.get("title_id")
        if not title_id:
            self._progress, self._progress_title = None, None
        elif title_id != self._progress_title or self._progress is None:
            try:
                self._progress = await self._client.get_title_progress(title_id)
                self._progress_title = title_id
            except Exception as err:  # pylint: disable=broad-exception-caught
                _LOG.debug("[%s] Title progress unavailable: %s", self.log_id, err)

    async def _update_friends(self) -> None:
        self._friends_online = await self._client.get_friends_online()

    async def _update_storage(self) -> None:
        for console in await self._client.get_consoles():
            if console["id"] == self._device_config.liveid:
                self._storage = console["storage"]
                return

    async def _quietly(self, coro) -> None:
        try:
            await coro
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.debug("[%s] Optional update failed: %s", self.log_id, err)

    async def _try_reconnect(self) -> bool:
        _LOG.info("[%s] Attempting reconnection...", self.log_id)
        if not await self._connect_client():
            return False
        await self._after_connect()
        _LOG.info("[%s] Reconnected successfully", self.log_id)
        self.push_update()
        self.events.emit(DeviceEvents.CONNECTED, self.identifier)
        return True

    async def disconnect(self) -> None:
        async with self._connect_lock:
            if self._library_task and not self._library_task.done():
                self._library_task.cancel()
            self._library_task = None
            if self._client:
                await self._client.close()
                self._client = None
            self._state = "UNAVAILABLE"
            await super().disconnect()

    def _persist_tokens(self, tokens: dict) -> None:
        self.update_config(tokens=tokens)

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------
    async def send_command(self, command: str) -> bool:
        if not self._client or not self._client.is_connected:
            return False
        liveid = self._device_config.liveid
        try:
            if command[:5].upper() == "TEXT:":
                await self._client.insert_text(liveid, command[5:])
                return True
            match command:
                case "POWER_ON":
                    await self._client.turn_on(liveid)
                case "POWER_OFF":
                    await self._client.turn_off(liveid)
                case "POWER_TOGGLE":
                    if self.player_state == "OFF":
                        await self._client.turn_on(liveid)
                    else:
                        await self._client.turn_off(liveid)
                case "REBOOT":
                    await self._client.reboot(liveid)
                case "HOME":
                    await self.go_home()
                case "GUIDE":
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
                    # The console reports its playback state, so this can toggle.
                    if self._console is not None and self._console["playback"] == "Playing":
                        await self._client.pause(liveid)
                    else:
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
                case "UNMUTE":
                    await self._client.unmute(liveid)
                case "NEXUS":
                    await self._client.press_button(liveid, "Nexus")
                case _:
                    _LOG.warning("[%s] Unknown command: %s", self.log_id, command)
                    return False
            return True
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.error("[%s] Command %s failed: %s", self.log_id, command, err)
            return False

    async def power_on(self) -> None:
        await self._client.turn_on(self._device_config.liveid)

    async def power_off(self) -> None:
        await self._client.turn_off(self._device_config.liveid)

    async def go_home(self) -> None:
        """Go to the dashboard (as Home Assistant does) and show Home right away."""
        await self._client.go_home(self._device_config.liveid)
        await self._quietly(self._update_profile())  # baseline: what was running when Home was pressed
        self._home = {"signature": self._activity_signature()}
        _LOG.info("[%s] Home", self.log_id)
        self.push_update()

    async def launch_app(self, one_store_product_id: str) -> None:
        await self._client.launch_app(self._device_config.liveid, one_store_product_id)
        self._clear_home("app launched from the Remote")

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
