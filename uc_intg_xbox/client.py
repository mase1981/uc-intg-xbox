"""
Xbox Live API client.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
import ssl

import certifi
import httpx
from pythonxbox.api.client import XboxLiveClient
from pythonxbox.api.provider.smartglass.models import (
    GuideTab,
    InputKeyType,
    VolumeDirection,
)
from pythonxbox.authentication.manager import AuthenticationManager
from pythonxbox.authentication.models import OAuth2TokenResponse

from uc_intg_xbox.const import OAUTH_REDIRECT_URI

_LOG = logging.getLogger(__name__)


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

    @property
    def xuid(self) -> str | None:
        return self._xuid

    @property
    def gamertag(self) -> str:
        return self._gamertag

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    async def connect(self, tokens: dict) -> dict | None:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self._session = httpx.AsyncClient(verify=ssl_context)

        self._auth_mgr = AuthenticationManager(
            self._session, self._client_id, self._client_secret, OAUTH_REDIRECT_URI
        )
        self._auth_mgr.oauth = OAuth2TokenResponse.model_validate(tokens)

        await self._auth_mgr.refresh_tokens()
        _LOG.info("Xbox tokens refreshed successfully")

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

    async def turn_on(self, liveid: str) -> None:
        try:
            await self._client.smartglass.wake_up(liveid)
        except httpx.HTTPStatusError as err:
            if err.response.status_code == 404:
                raise ValueError(
                    "Console not reachable. Verify Sleep mode is enabled in console settings."
                ) from err
            raise

    async def turn_off(self, liveid: str) -> None:
        await self._client.smartglass.turn_off(liveid)

    async def press_button(self, liveid: str, button: str) -> None:
        button_enum = InputKeyType(button)
        await self._client.smartglass.press_button(liveid, button_enum)

    async def change_volume(self, liveid: str, direction: str) -> None:
        direction_enum = VolumeDirection(direction)
        await self._client.smartglass.volume(liveid, direction_enum)

    async def mute(self, liveid: str) -> None:
        await self._client.smartglass.mute(liveid)

    async def show_guide(self, liveid: str) -> None:
        await self._client.smartglass.show_guide_tab(liveid, GuideTab.Guide)

    async def go_home(self, liveid: str) -> None:
        await self._client.smartglass.go_home(liveid)

    async def go_back(self, liveid: str) -> None:
        await self._client.smartglass.go_back(liveid)

    async def play(self, liveid: str) -> None:
        await self._client.smartglass.play(liveid)

    async def pause(self, liveid: str) -> None:
        await self._client.smartglass.pause(liveid)

    async def next_track(self, liveid: str) -> None:
        await self._client.smartglass.next(liveid)

    async def previous_track(self, liveid: str) -> None:
        await self._client.smartglass.previous(liveid)

    async def get_presence(self, liveid: str) -> dict | None:
        try:
            batch = await self._client.people.get_friends_own_batch([self._xuid])
            people = getattr(batch, "people", None) or []
            profile = next((p for p in people if getattr(p, "xuid", None) == self._xuid), None)

            if not profile:
                return None

            presence_state = getattr(profile, "presence_state", "Offline")

            if presence_state == "Offline":
                return {"state": "OFF", "title": "Offline", "image": ""}

            presence_text = getattr(profile, "presence_text", None)
            presence_details = getattr(profile, "presence_details", None) or []

            for detail in presence_details:
                detail_state = getattr(detail, "state", None)
                is_primary = getattr(detail, "is_primary", False)
                is_game = getattr(detail, "is_game", False)
                title_id = getattr(detail, "title_id", None)

                if detail_state == "Active" and title_id and is_game and is_primary:
                    try:
                        title_response = await self._client.titlehub.get_title_info(title_id)
                        titles = getattr(title_response, "titles", None) or []
                        if titles:
                            title_data = titles[0]
                            return {
                                "state": "PLAYING",
                                "title": title_data.name,
                                "image": getattr(title_data, "display_image", ""),
                            }
                    except Exception as err:
                        _LOG.error("Failed to fetch title info for %s: %s", title_id, err)

            return {"state": "ON", "title": presence_text or "Online", "image": ""}

        except Exception as err:
            _LOG.debug("Failed to get presence: %s", err)
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
        for game in games:
            if not game.get("title_id"):
                continue
            try:
                title_response = await self._client.titlehub.get_title_info(game["title_id"])
                titles = getattr(title_response, "titles", None) or []
                if titles:
                    game["image"] = getattr(titles[0], "display_image", "") or ""
                    name = getattr(titles[0], "name", None)
                    if name:
                        game["name"] = name
            except Exception:
                pass
        return games

    async def launch_app(self, liveid: str, one_store_product_id: str) -> None:
        await self._client.smartglass.launch_app(liveid, one_store_product_id)

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
        await self._auth_mgr.request_tokens(code)
        self._client = XboxLiveClient(self._auth_mgr)
        self._xuid = self._client.xuid
        return self._auth_mgr.oauth.model_dump(mode="json")
