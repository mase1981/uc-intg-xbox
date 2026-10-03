"""
Xbox Live API client.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
import ssl
from datetime import datetime

import certifi
import httpx
from pydantic import ValidationError
from pythonxbox.api.client import XboxLiveClient
from pythonxbox.api.provider.catalog.const import SYSTEM_PFN_ID_MAP
from pythonxbox.api.provider.catalog.models import AlternateIdType
from pythonxbox.api.provider.smartglass.models import (
    GuideTab,
    InputKeyType,
    VolumeDirection,
)
from pythonxbox.authentication.manager import AuthenticationManager
from pythonxbox.authentication.models import OAuth2TokenResponse

from uc_intg_xbox.const import OAUTH_REDIRECT_URI, TITLEHUB_CONCURRENCY

_LOG = logging.getLogger(__name__)

# Same picks as Home Assistant: platform names and party join restrictions.
PLATFORM_NAMES = {
    "Android": "Android",
    "iOS": "iOS",
    "Nintendo": "Nintendo Switch",
    "Scarlett": "Xbox Series X|S",
    "WindowsOneCore": "Windows",
    "Xbox360": "Xbox 360",
    "XboxOne": "Xbox One",
}
JOIN_RESTRICTIONS = {"local": "Invite only", "followed": "Joinable"}
_IMAGE_PURPOSES = ("FeaturePromotionalSquareArt", "Tile", "Logo", "BoxArt")


def _https(url: str) -> str:
    return "https://" + url[7:] if url and url.startswith("http://") else (url or "")


def _of(current, total) -> str:
    return f"{current} / {total}" if total else str(current)


def _square_image(images) -> str:
    """Best square artwork of at least 300 px, in Home Assistant's order of preference."""
    for purpose in _IMAGE_PURPOSES:
        for image in images or []:
            if (
                getattr(image, "image_purpose", None) == purpose
                and getattr(image, "width", 0) == getattr(image, "height", -1)
                and getattr(image, "width", 0) >= 300
            ):
                return _https(getattr(image, "uri", ""))
    return ""


class XboxClient:
    """Xbox Live API client wrapper."""

    def __init__(self, client_id: str, client_secret: str = ""):
        self._client_id = client_id
        self._client_secret = client_secret
        self._session: httpx.AsyncClient | None = None
        self._auth_mgr: AuthenticationManager | None = None
        self._client: XboxLiveClient | None = None
        self._xuid: str | None = None
        self._gamertag: str = "Xbox User"
        self._app_cache: dict[str, dict] = {}  # focus app id -> {"title", "image", "is_game"}
        self._catalog_logged: set[str] = set()  # log a catalog problem once per app

    @property
    def xuid(self) -> str | None:
        return self._xuid

    @property
    def gamertag(self) -> str:
        return self._gamertag

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    async def connect(self, tokens: dict, on_tokens_refreshed=None) -> dict | None:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self._session = httpx.AsyncClient(verify=ssl_context)

        self._auth_mgr = AuthenticationManager(
            self._session, self._client_id, self._client_secret, OAUTH_REDIRECT_URI
        )
        self._auth_mgr.oauth = OAuth2TokenResponse.model_validate(tokens)

        await self._auth_mgr.refresh_tokens()
        _LOG.info("Xbox tokens refreshed successfully")

        if on_tokens_refreshed:
            on_tokens_refreshed(self._auth_mgr.oauth.model_dump(mode="json"))

        self._client = XboxLiveClient(self._auth_mgr)
        self._xuid = self._client.xuid

        try:
            profile = await self._client.profile.get_profile_by_xuid(self._xuid)
            for setting in profile.profile_users[0].settings:
                if setting.id == "ModernGamertag":
                    self._gamertag = setting.value
                    break
        except Exception as err:
            _LOG.warning("Could not retrieve gamertag: %s", err)

        return self._auth_mgr.oauth.model_dump(mode="json")

    async def refresh_tokens(self) -> dict | None:
        if not self._auth_mgr:
            return None
        try:
            await self._auth_mgr.refresh_tokens()
            return self._auth_mgr.oauth.model_dump(mode="json")
        except Exception as err:
            _LOG.error("Token refresh failed: %s", err)
            return None

    async def close(self) -> None:
        if self._session and not self._session.is_closed:
            await self._session.aclose()
        self._session = None
        self._client = None
        self._auth_mgr = None

    async def test_connection(self) -> bool:
        try:
            await self._client.people.get_friends_own_batch([self._xuid])
            return True
        except Exception:
            return False

    async def _send_command(self, coro) -> None:
        try:
            await coro
        except ValidationError as err:
            _LOG.debug("Command delivered; response validation skipped: %s", err)

    async def turn_on(self, liveid: str) -> None:
        try:
            await self._send_command(self._client.smartglass.wake_up(liveid))
        except httpx.HTTPStatusError as err:
            if err.response.status_code == 404:
                raise ValueError(
                    "Console not reachable. Verify Sleep mode is enabled in console settings."
                ) from err
            raise

    async def turn_off(self, liveid: str) -> None:
        await self._send_command(self._client.smartglass.turn_off(liveid))

    async def press_button(self, liveid: str, button: str) -> None:
        button_enum = InputKeyType(button)
        await self._send_command(self._client.smartglass.press_button(liveid, button_enum))

    async def change_volume(self, liveid: str, direction: str) -> None:
        direction_enum = VolumeDirection(direction)
        await self._send_command(self._client.smartglass.volume(liveid, direction_enum))

    async def mute(self, liveid: str) -> None:
        await self._send_command(self._client.smartglass.mute(liveid))

    async def show_guide(self, liveid: str) -> None:
        await self._send_command(self._client.smartglass.show_guide_tab(liveid, GuideTab.Guide))

    async def go_home(self, liveid: str) -> None:
        await self._send_command(self._client.smartglass.go_home(liveid))

    async def go_back(self, liveid: str) -> None:
        await self._send_command(self._client.smartglass.go_back(liveid))

    async def play(self, liveid: str) -> None:
        await self._send_command(self._client.smartglass.play(liveid))

    async def pause(self, liveid: str) -> None:
        await self._send_command(self._client.smartglass.pause(liveid))

    async def next_track(self, liveid: str) -> None:
        await self._send_command(self._client.smartglass.next(liveid))

    async def previous_track(self, liveid: str) -> None:
        await self._send_command(self._client.smartglass.previous(liveid))

    async def get_presence(self, liveid: str) -> dict | None:
        try:
            batch = await self._client.people.get_friends_own_batch([self._xuid])
            people = getattr(batch, "people", None) or []
            profile = next((p for p in people if getattr(p, "xuid", None) == self._xuid), None)

            if not profile:
                _LOG.debug("Presence: own XUID %s not found in %d people", self._xuid, len(people))
                return None

            presence_state = getattr(profile, "presence_state", "Offline")

            if presence_state == "Offline":
                return {"state": "OFF", "title": "Offline", "image": ""}

            presence_text = getattr(profile, "presence_text", None)
            presence_details = getattr(profile, "presence_details", None) or []
            _LOG.debug("Presence: state=%s, text=%s, details=%d",
                       presence_state, presence_text, len(presence_details))

            for detail in presence_details:
                detail_state = getattr(detail, "state", None)
                is_primary = getattr(detail, "is_primary", False)
                is_game = getattr(detail, "is_game", False)
                title_id = getattr(detail, "title_id", None)
                _LOG.debug("Presence detail: state=%s, is_game=%s, is_primary=%s, title_id=%s",
                           detail_state, is_game, is_primary, title_id)

                if detail_state == "Active" and title_id and is_game and is_primary:
                    try:
                        title_response = await self._client.titlehub.get_title_info(title_id)
                        titles = getattr(title_response, "titles", None) or []
                        if titles:
                            title_data = titles[0]
                            image = getattr(title_data, "display_image", "") or ""
                            if image.startswith("http://"):
                                image = "https://" + image[7:]
                            return {
                                "state": "PLAYING",
                                "title": title_data.name,
                                "image": image,
                            }
                    except Exception as err:
                        _LOG.error("Failed to fetch title info for %s: %s", title_id, err)

            return {"state": "ON", "title": presence_text or "Online", "image": ""}

        except Exception as err:
            _LOG.debug("Failed to get presence: %s (%s)", err, type(err).__name__)
            return None

    async def get_installed_apps(self, liveid: str) -> list[dict]:
        try:
            result = await self._client.smartglass.get_installed_apps(liveid)
            apps = result.result if result else []
            games = []
            for app in apps:
                if not app.one_store_product_id:
                    continue
                if app.content_type and app.content_type != "Game":
                    continue
                games.append({
                    "one_store_product_id": app.one_store_product_id,
                    "title_id": str(app.title_id) if app.title_id else "",
                    "name": app.name or f"Game {app.title_id or 'Unknown'}",
                    "image": "",
                })
            return await self._enrich_game_images(games)
        except Exception as err:
            _LOG.debug("Failed to get installed apps: %s", err)
            return []

    async def _enrich_game_images(self, games: list[dict]) -> list[dict]:
        semaphore = asyncio.Semaphore(TITLEHUB_CONCURRENCY)

        async def enrich(game: dict) -> None:
            if not game.get("title_id"):
                return
            try:
                async with semaphore:
                    title_response = await self._client.titlehub.get_title_info(game["title_id"])
                titles = getattr(title_response, "titles", None) or []
                if titles:
                    image = getattr(titles[0], "display_image", "") or ""
                    if image.startswith("http://"):
                        image = "https://" + image[7:]
                    game["image"] = image
                    name = getattr(titles[0], "name", None)
                    if name:
                        game["name"] = name
            except Exception:
                pass

        await asyncio.gather(*(enrich(game) for game in games))
        return games

    async def launch_app(self, liveid: str, one_store_product_id: str) -> None:
        await self._send_command(self._client.smartglass.launch_app(liveid, one_store_product_id))

    # ------------------------------------------------------------------
    # Console status (the console's own state, as Home Assistant reads it)
    # ------------------------------------------------------------------
    async def get_consoles(self) -> list[dict]:
        """Consoles on the account, with their storage devices."""
        result = await self._client.smartglass.get_console_list()
        consoles = []
        for console in getattr(result, "result", None) or []:
            storage = [
                {
                    "name": device.storage_device_name,
                    "total": device.total_space_bytes,
                    "free": device.free_space_bytes,
                }
                for device in (console.storage_devices or [])
            ]
            consoles.append({
                "id": console.id,
                "name": console.name,
                "type": str(getattr(console, "console_type", "")),
                "storage": storage,
            })
        return consoles

    async def get_console_status(self, liveid: str) -> dict:
        """Power state, playback state and the app in focus on this console."""
        status = await self._client.smartglass.get_console_status(liveid)
        aumid = status.focus_app_aumid or ""
        app = await self._app_details(aumid) if aumid else None
        return {
            "power": str(status.power_state.value if hasattr(status.power_state, "value") else status.power_state),
            "playback": str(status.playback_state.value if hasattr(status.playback_state, "value") else status.playback_state),
            "focus_app": aumid,
            "app": app,
        }

    async def _app_details(self, aumid: str) -> dict | None:
        """Look up the focused app in the Microsoft Store catalog (cached per app)."""
        app_id = aumid.split("!", maxsplit=1)[0]
        if app_id in self._app_cache:
            return self._app_cache[app_id]
        id_type = AlternateIdType.PACKAGE_FAMILY_NAME
        lookup_id = app_id
        if app_id in SYSTEM_PFN_ID_MAP:
            id_type = AlternateIdType.LEGACY_XBOX_PRODUCT_ID
            lookup_id = SYSTEM_PFN_ID_MAP[app_id][id_type]
        details = None
        try:
            result = await self._client.catalog.get_product_from_alternate_id(lookup_id, id_type)
            products = getattr(result, "products", None) or []
            if not products and app_id not in self._catalog_logged:
                self._catalog_logged.add(app_id)
                _LOG.info("No Store catalog entry for %s, using presence for the title", app_id)
            if products:
                product = products[0]
                props = (product.localized_properties or [None])[0]
                if props is not None:
                    details = {
                        "title": props.product_title or props.short_title or "",
                        "image": _square_image(props.images),
                        "is_game": getattr(product, "product_family", "") == "Games",
                    }
        except Exception as err:  # pylint: disable=broad-exception-caught
            log = _LOG.debug if app_id in self._catalog_logged else _LOG.warning
            self._catalog_logged.add(app_id)
            log("Catalog lookup failed for %s: %s", app_id, err)
            return None  # not cached: try again next time
        self._app_cache[app_id] = details or {}
        return details

    # ------------------------------------------------------------------
    # Profile, friends and the current game's progress
    # ------------------------------------------------------------------
    async def get_profile(self) -> dict | None:
        """Own profile: status, gamerscore, followers, party and the active title."""
        response = await self._client.people.get_friend_by_xuid(self._xuid)
        people = getattr(response, "people", None) or []
        if not people:
            return None
        person = people[0]
        detail = getattr(person, "detail", None)
        party = getattr(person, "multiplayer_summary", None)
        party_details = getattr(party, "party_details", None) or []
        active = next(
            (d for d in person.presence_details or [] if d.state == "Active" and d.is_game),
            None,
        ) or next((d for d in person.presence_details or [] if d.state == "Active"), None)
        last_seen = getattr(person, "last_seen_date_time_utc", None)
        return {
            "status": person.presence_text or person.presence_state or "",
            "online": person.presence_state == "Online",
            "gamerscore": person.gamer_score,
            "followers": detail.follower_count if detail else None,
            "following": detail.following_count if detail else None,
            "in_party": bool(party.in_party) if party else None,
            "join_restriction": (
                JOIN_RESTRICTIONS.get(party_details[0].join_restriction, party_details[0].join_restriction)
                if party_details else None
            ),
            "platform": PLATFORM_NAMES.get(active.device, active.device) if active else None,
            "title_id": active.title_id if active and active.is_game else None,
            "last_seen": last_seen if isinstance(last_seen, datetime) else None,
            "gamerpic": _https(getattr(person, "display_pic_raw", "") or ""),
        }

    async def get_friends_online(self) -> int:
        response = await self._client.people.get_friends_own()
        return sum(1 for friend in getattr(response, "people", None) or [] if friend.presence_state == "Online")

    async def get_title_progress(self, title_id: str) -> dict | None:
        """Name, artwork, and achievements and gamerscore earned in one title."""
        response = await self._client.titlehub.get_title_info(title_id)
        titles = getattr(response, "titles", None) or []
        if not titles:
            return None
        title = titles[0]
        info = {"name": title.name or "", "image": _https(title.display_image or "")}
        achievement = getattr(title, "achievement", None)
        if achievement is not None:
            info.update({
                # Some titles report no totals (0); show only what was earned then.
                "achievements": _of(achievement.current_achievements, achievement.total_achievements),
                "gamerscore": _of(achievement.current_gamerscore, achievement.total_gamerscore),
                "progress": int(achievement.progress_percentage),
            })
        return info

    # ------------------------------------------------------------------
    # Extra console commands (Home Assistant's remote set)
    # ------------------------------------------------------------------
    async def reboot(self, liveid: str) -> None:
        await self._send_command(self._client.smartglass.reboot(liveid))

    async def unmute(self, liveid: str) -> None:
        await self._send_command(self._client.smartglass.unmute(liveid))

    async def insert_text(self, liveid: str, text: str) -> None:
        await self._send_command(self._client.smartglass.insert_text(liveid, text))

    def generate_auth_url(self) -> str:
        query_params = {
            "client_id": self._client_id,
            "response_type": "code",
            "approval_prompt": "auto",
            "scope": "Xboxlive.signin Xboxlive.offline_access",
            "redirect_uri": OAUTH_REDIRECT_URI,
        }
        return str(httpx.URL(
            "https://login.live.com/oauth20_authorize.srf", params=query_params
        ))

    async def exchange_code(self, code: str) -> dict | None:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self._session = httpx.AsyncClient(verify=ssl_context)
        self._auth_mgr = AuthenticationManager(
            self._session, self._client_id, self._client_secret, OAUTH_REDIRECT_URI
        )
        try:
            await self._auth_mgr.request_tokens(code)
        except httpx.HTTPStatusError as err:
            body = err.response.text if err.response else "no response body"
            _LOG.error("Token exchange HTTP error: %s - %s", err.response.status_code, body)
            raise
        self._client = XboxLiveClient(self._auth_mgr)
        self._xuid = self._client.xuid
        return self._auth_mgr.oauth.model_dump(mode="json")
