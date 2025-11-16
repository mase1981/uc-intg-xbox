"""
Xbox client wrapper for Unfolded Circle integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
import httpx
import ssl
import certifi
from pythonxbox.api.client import XboxLiveClient
from pythonxbox.authentication.manager import AuthenticationManager
from pythonxbox.authentication.models import OAuth2TokenResponse
from pythonxbox.api.provider.smartglass.models import (
    InputKeyType,
    VolumeDirection,
)
from pythonxbox.scripts import CLIENT_ID, CLIENT_SECRET

_LOG = logging.getLogger("XBOX_CLIENT")
OAUTH2_DESKTOP_REDIRECT_URI = "https://login.live.com/oauth20_desktop.srf"

class XboxClient:
    def __init__(self, live_id: str):
        self.live_id = live_id
        self.client: XboxLiveClient | None = None
        self.session: httpx.AsyncClient | None = None
        self.xuid: str | None = None
        self.gamertag: str = "Xbox User"

    @classmethod
    async def from_config(cls, config, existing_session: httpx.AsyncClient = None):
        instance = cls(config.liveid)
        
        try:
            if existing_session:
                instance.session = existing_session
            else:
                ssl_context = ssl.create_default_context(cafile=certifi.where())
                instance.session = httpx.AsyncClient(verify=ssl_context, timeout=30.0)

            auth_mgr = AuthenticationManager(
                instance.session,
                CLIENT_ID,
                CLIENT_SECRET,
                OAUTH2_DESKTOP_REDIRECT_URI,
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
        _LOG.info(f"Sending power on (wake_up) to Xbox Live ID: {self.live_id}")
        try:
            await self.client.smartglass.wake_up(self.live_id)
            _LOG.info("Power on command sent successfully.")
        except Exception as e:
            _LOG.exception("Failed to send power on command", exc_info=e)
            raise

    async def turn_off(self):
        _LOG.info(f"Sending power off to Xbox Live ID: {self.live_id}")
        try:
            await self.client.smartglass.turn_off(self.live_id)
            _LOG.info("Power off command sent.")
        except Exception as e:
            _LOG.exception("Failed to send power off command", exc_info=e)
            raise

    async def volume(self, direction: str):
        _LOG.info(f"Sending Volume {direction} to {self.live_id}")
        try:
            direction_enum = VolumeDirection(direction)
            await self.client.smartglass.volume(self.live_id, direction_enum)
            _LOG.info(f"Volume {direction} command sent successfully.")
        except Exception as e:
            _LOG.exception("Failed to change volume", exc_info=e)
            raise

    async def mute(self):
        _LOG.info(f"Sending Mute to {self.live_id}")
        try:
            await self.client.smartglass.mute(self.live_id)
            _LOG.info("Mute command sent successfully.")
        except Exception as e:
            _LOG.exception("Failed to mute", exc_info=e)
            raise

    async def unmute(self):
        _LOG.info(f"Sending Unmute to {self.live_id}")
        try:
            await self.client.smartglass.unmute(self.live_id)
            _LOG.info("Unmute command sent successfully.")
        except Exception as e:
            _LOG.exception("Failed to unmute", exc_info=e)
            raise

    async def press_button(self, button: str):
        _LOG.info(f"Sending button press: '{button}' to {self.live_id}")
        try:
            button_enum = InputKeyType(button)
            await self.client.smartglass.press_button(self.live_id, button_enum)
            _LOG.info(f"Button '{button}' pressed successfully.")
        except ValueError:
            _LOG.error(f"Unknown button command: {button}")
            raise ValueError(f"Unknown button command: {button}")
        except Exception as e:
            _LOG.exception(f"Failed to press button '{button}'", exc_info=e)
            raise

    async def insert_text(self, text: str):
        _LOG.info(f"Sending text input: '{text}' to {self.live_id}")
        try:
            await self.client.smartglass.insert_text(self.live_id, text)
            _LOG.info(f"Text '{text}' sent successfully.")
        except Exception as e:
            _LOG.exception(f"Failed to send text '{text}'", exc_info=e)
            raise

    async def launch_app(self, product_id: str):
        _LOG.info(f"Launching app '{product_id}' on {self.live_id}")
        try:
            if product_id == "Home":
                await self.client.smartglass.go_home(self.live_id)
            else:
                await self.client.smartglass.launch_app(self.live_id, product_id)
            _LOG.info(f"App '{product_id}' launched successfully.")
        except Exception as e:
            _LOG.exception(f"Failed to launch app '{product_id}'", exc_info=e)
            raise

    async def get_console_status(self):
        try:
            status = await self.client.smartglass.get_console_status(self.live_id)
            return status
        except Exception as e:
            _LOG.exception("Failed to get console status", exc_info=e)
            return None

    async def get_presence(self):
        try:
            resp = await self.client.people.get_friends_own_batch([self.xuid])
            if resp.people:
                return resp.people[0]
            return None
        except Exception as e:
            _LOG.exception("Failed to get presence", exc_info=e)
            return None

    async def get_installed_apps(self):
        try:
            apps = await self.client.smartglass.get_installed_apps(self.live_id)
            return apps
        except Exception as e:
            _LOG.exception("Failed to get installed apps", exc_info=e)
            return None

    async def close(self):
        if self.session and not self.session.is_closed:
            await self.session.aclose()