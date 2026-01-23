"""
Xbox client wrapper for Unfolded Circle integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
import httpx
import ssl
import certifi
from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.authentication.models import OAuth2TokenResponse
from xbox.webapi.api.provider.smartglass.models import (
    InputKeyType,
    VolumeDirection,
)
_LOG = logging.getLogger("XBOX_CLIENT")
OAUTH2_REDIRECT_URI = "http://localhost:8765/callback"

class XboxClient:
    def __init__(self, live_id: str):
        self.live_id = live_id
        self.client: XboxLiveClient | None = None
        self.session: httpx.AsyncClient | None = None
        self.xuid: str | None = None
        self.gamertag: str = "Xbox User"
        self._last_known_state: str = "UNKNOWN"

    @classmethod
    async def from_config(cls, config, existing_session: httpx.AsyncClient = None):
        instance = cls(config.liveid)

        try:
            if existing_session:
                instance.session = existing_session
            else:
                ssl_context = ssl.create_default_context(cafile=certifi.where())
                instance.session = httpx.AsyncClient(verify=ssl_context)

            # Use user-provided Azure App credentials from config
            auth_mgr = AuthenticationManager(
                instance.session,
                config.client_id,
                config.client_secret,
                OAUTH2_REDIRECT_URI,
            )
            auth_mgr.oauth = OAuth2TokenResponse.model_validate(config.tokens)
            
            await auth_mgr.refresh_tokens()
            _LOG.info("Successfully refreshed Xbox authentication tokens")
            
            instance.client = XboxLiveClient(auth_mgr)
            instance.xuid = instance.client.xuid
            
            try:
                profile = await instance.client.profile.get_profile_by_xuid(instance.xuid)
                for setting in profile.profile_users[0].settings:
                    if setting.id == "ModernGamertag":
                        instance.gamertag = setting.value
                        _LOG.info(f"Retrieved gamertag: {instance.gamertag}")
                        break
            except Exception as e:
                _LOG.warning(f"Could not retrieve gamertag: {e}")
            
            return instance, auth_mgr.oauth.model_dump()

        except Exception as e:
            _LOG.exception("Failed to create Xbox client", exc_info=e)
            if instance.session and not existing_session:
                await instance.session.aclose()
            return None, None

    async def turn_on(self):
        _LOG.info(f"Sending power on to Xbox Live ID: {self.live_id}")
        try:
            await self.client.smartglass.wake_up(self.live_id)
            _LOG.info("Power on command sent successfully")
            self._last_known_state = "ON"
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                _LOG.error("Xbox API returned 404 - Console may be in Energy Saving mode or not reachable. Ensure console is in Sleep mode.")
                raise ValueError("Console not reachable. Verify Sleep mode is enabled in console settings.")
            _LOG.exception("HTTP error sending power on command", exc_info=e)
            raise
        except Exception as e:
            _LOG.exception("Failed to send power on command", exc_info=e)
            raise

    async def turn_off(self):
        _LOG.info(f"Sending power off to Xbox Live ID: {self.live_id}")
        try:
            await self.client.smartglass.turn_off(self.live_id)
            _LOG.info("Power off command sent")
            self._last_known_state = "OFF"
        except Exception as e:
            _LOG.exception("Failed to send power off command", exc_info=e)
            raise

    async def change_volume(self, direction: str):
        _LOG.info(f"Sending Volume {direction} to {self.live_id}")
        try:
            direction_enum = VolumeDirection(direction)
            await self.client.smartglass.change_volume(self.live_id, direction_enum)
            _LOG.info(f"Volume {direction} command sent successfully")
        except Exception as e:
            _LOG.exception("Failed to change volume", exc_info=e)
            raise

    async def mute(self):
        _LOG.info(f"Sending Mute to {self.live_id}")
        try:
            await self.client.smartglass.mute(self.live_id)
            _LOG.info("Mute command sent successfully")
        except Exception as e:
            _LOG.exception("Failed to mute", exc_info=e)
            raise

    async def unmute(self):
        _LOG.info(f"Sending Unmute to {self.live_id}")
        try:
            await self.client.smartglass.unmute(self.live_id)
            _LOG.info("Unmute command sent successfully")
        except Exception as e:
            _LOG.exception("Failed to unmute", exc_info=e)
            raise

    async def press_button(self, button: str):
        _LOG.info(f"Sending button press: '{button}' to {self.live_id}")
        try:
            button_enum = InputKeyType(button)
            await self.client.smartglass.press_button(self.live_id, button_enum)
            _LOG.info(f"Button '{button}' pressed successfully")
        except ValueError:
            _LOG.error(f"Unknown button command: {button}")
            raise ValueError(f"Unknown button command: {button}")
        except Exception as e:
            _LOG.exception(f"Failed to press button '{button}'", exc_info=e)
            raise

    async def play(self):
        _LOG.info(f"Sending Play to {self.live_id}")
        try:
            await self.client.smartglass.play(self.live_id)
            _LOG.info("Play command sent successfully")
        except Exception as e:
            _LOG.exception("Failed to send play command", exc_info=e)
            raise

    async def pause(self):
        _LOG.info(f"Sending Pause to {self.live_id}")
        try:
            await self.client.smartglass.pause(self.live_id)
            _LOG.info("Pause command sent successfully")
        except Exception as e:
            _LOG.exception("Failed to send pause command", exc_info=e)
            raise

    async def next_track(self):
        _LOG.info(f"Sending Next Track to {self.live_id}")
        try:
            await self.client.smartglass.next(self.live_id)
            _LOG.info("Next track command sent successfully")
        except Exception as e:
            _LOG.exception("Failed to send next track command", exc_info=e)
            raise

    async def previous_track(self):
        _LOG.info(f"Sending Previous Track to {self.live_id}")
        try:
            await self.client.smartglass.previous(self.live_id)
            _LOG.info("Previous track command sent successfully")
        except Exception as e:
            _LOG.exception("Failed to send previous track command", exc_info=e)
            raise

    async def get_console_state(self):
        try:
            batch = await self.client.people.get_friends_own_batch([self.xuid])
            people = getattr(batch, "people", None) or []
            
            profile = next((p for p in people if getattr(p, "xuid", None) == self.xuid), None)
            
            if not profile:
                _LOG.warning("Could not find own profile in batch")
                return self._last_known_state
            
            presence_state = getattr(profile, "presence_state", "Offline")
            
            if presence_state == "Offline":
                self._last_known_state = "OFF"
                return "OFF"
            
            self._last_known_state = "ON"
            return "ON"
            
        except Exception as e:
            _LOG.debug(f"Failed to get console state: {e}")
            return self._last_known_state

    async def get_presence_and_title(self):
        try:
            batch = await self.client.people.get_friends_own_batch([self.xuid])
            people = getattr(batch, "people", None) or []
            
            profile = next((p for p in people if getattr(p, "xuid", None) == self.xuid), None)
            
            if not profile:
                _LOG.warning(f"Could not find own profile in batch")
                return None
            
            presence_state = getattr(profile, "presence_state", "Offline")
            
            if presence_state == "Offline":
                self._last_known_state = "OFF"
                return {
                    "state": "OFF",
                    "title": "Offline",
                    "image": ""
                }
            
            self._last_known_state = "ON"
            presence_text = getattr(profile, "presence_text", None)
            presence_details = getattr(profile, "presence_details", None) or []
            
            for detail in presence_details:
                detail_state = getattr(detail, "state", None)
                is_primary = getattr(detail, "is_primary", False)
                is_game = getattr(detail, "is_game", False)
                title_id = getattr(detail, "title_id", None)
                
                if detail_state == "Active" and title_id and is_game and is_primary:
                    try:
                        title_response = await self.client.titlehub.get_title_info(title_id)
                        titles = getattr(title_response, "titles", None) or []
                        
                        if titles:
                            title_data = titles[0]
                            return {
                                "state": "PLAYING",
                                "title": title_data.name,
                                "image": getattr(title_data, "display_image", "")
                            }
                    except Exception as e:
                        _LOG.error(f"Failed to fetch title info for {title_id}: {e}")
            
            return {
                "state": "ON",
                "title": presence_text or "Online",
                "image": ""
            }
            
        except Exception as e:
            _LOG.exception("Failed to get presence and title", exc_info=e)
            return None

    async def close(self):
        if self.session and not self.session.is_closed:
            await self.session.aclose()