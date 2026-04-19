"""
Xbox Live API client.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
import ssl

import certifi
import httpx
from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.api.provider.smartglass.models import (
    GuideTab,
    InputKeyType,
    VolumeDirection,
)
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.authentication.models import OAuth2TokenResponse

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
        await self._client.smartglass.change_volume(liveid, direction_enum)

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

    async def get_installed_games(self) -> list[dict]:
        try:
            from xbox.webapi.api.provider.titlehub.models import TitleFields
            result = await self._client.titlehub.get_title_history(
                self._xuid,
                fields=[TitleFields.IMAGE, TitleFields.DETAIL, TitleFields.PRODUCT_ID],
                max_items=100,
            )
            titles = getattr(result, "titles", None) or []
            games = []
            for title in titles:
                devices = getattr(title, "devices", None) or []
                is_xbox = any("Xbox" in d or "Console" in d for d in devices)
                if not is_xbox:
                    continue
                name = getattr(title, "name", None)
                title_id = getattr(title, "title_id", None)
                image = getattr(title, "display_image", "")
                pfn = getattr(title, "pfn", None)
                if name and title_id:
                    games.append({
                        "title_id": str(title_id),
                        "name": name,
                        "image": image,
                        "pfn": pfn or "",
                    })
            return games
        except Exception as err:
            _LOG.debug("Failed to get installed games: %s", err)
            return []

    async def launch_game(self, liveid: str, title_id: str) -> None:
        try:
            from xbox.webapi.api.provider.titlehub.models import TitleFields
            title_response = await self._client.titlehub.get_title_info(
                title_id,
                fields=[TitleFields.DETAIL, TitleFields.PRODUCT_ID],
            )
            titles = getattr(title_response, "titles", None) or []

            one_store_product_id = None
            if titles:
                detail = getattr(titles[0], "detail", None)
                if detail:
                    availabilities = getattr(detail, "availabilities", None) or []
                    for avail in availabilities:
                        sku_id = getattr(avail, "sku_id", None)
                        if sku_id:
                            one_store_product_id = sku_id
                            break

                if not one_store_product_id:
                    product_id = getattr(titles[0], "windows_phone_product_id", None)
                    if product_id:
                        one_store_product_id = product_id

            if one_store_product_id:
                await self._client.smartglass.launch_app(liveid, one_store_product_id)
            else:
                _LOG.warning("Could not find launchable product for title %s, trying pfn", title_id)
                pfn = getattr(titles[0], "pfn", None) if titles else None
                if pfn:
                    await self._client.smartglass.launch_app(liveid, pfn)
                else:
                    _LOG.error("No launch method available for title %s", title_id)
        except Exception as err:
            _LOG.error("Failed to launch game %s: %s", title_id, err)
            raise

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
