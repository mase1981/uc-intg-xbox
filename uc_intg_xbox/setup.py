"""
Xbox setup module for Unfolded Circle integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
import asyncio
import httpx
import ssl
import certifi
from ucapi import (
    DriverSetupRequest,
    AbortDriverSetup,
    SetupComplete,
    SetupError,
    IntegrationSetupError,
    RequestUserInput,
)
from uc_intg_xbox.config import XboxConfig
from uc_intg_xbox.auth import XboxAuth

_LOG = logging.getLogger("XBOX_SETUP")

class XboxSetup:
    def __init__(self, api, config: XboxConfig):
        self.api = api
        self.config = config
        self.auth_session: httpx.AsyncClient | None = None
        self.device_code_data: dict | None = None
        self.polling_task: asyncio.Task | None = None

    async def handle_command(self, request):
        if isinstance(request, DriverSetupRequest):
            if request.reconfigure or not self.config.tokens:
                self.config.liveid = request.setup_data.get("liveid", "").strip()

                if not self.config.liveid:
                    return SetupError(IntegrationSetupError.INVALID_INPUT)

                _LOG.info("Live ID captured. Starting Device Code Flow authentication.")
                ssl_context = ssl.create_default_context(cafile=certifi.where())
                self.auth_session = httpx.AsyncClient(verify=ssl_context)
                auth_handler = XboxAuth(self.auth_session)

                # Request device code from Microsoft
                self.device_code_data = await auth_handler.request_device_code()

                if not self.device_code_data:
                    _LOG.error("Failed to obtain device code")
                    await self._cleanup_session()
                    return SetupError(IntegrationSetupError.OTHER)

                user_code = self.device_code_data.get("user_code", "")
                verification_uri = self.device_code_data.get("verification_uri", "")
                expires_in = self.device_code_data.get("expires_in", 900)

                _LOG.info(f"Device code flow initiated. User code: {user_code}")

                # Start background polling task
                device_code = self.device_code_data.get("device_code")
                interval = self.device_code_data.get("interval", 5)
                self.polling_task = asyncio.create_task(
                    self._poll_and_complete(auth_handler, device_code, interval, expires_in)
                )

                return RequestUserInput(
                    {"en": "Xbox Device Authentication"},
                    [
                        {
                            "id": "instructions",
                            "label": {"en": "Authentication Instructions"},
                            "field": {
                                "label": {
                                    "value": {
                                        "en": f"Please complete authentication on another device:\n\n"
                                              f"1. Visit: {verification_uri}\n"
                                              f"2. Enter code: {user_code}\n"
                                              f"3. Sign in with your Microsoft account\n"
                                              f"4. Wait for authentication to complete\n\n"
                                              f"Code expires in {expires_in // 60} minutes."
                                    }
                                }
                            }
                        },
                        {
                            "id": "verification_uri",
                            "label": {"en": "Verification URL"},
                            "field": {
                                "text": {
                                    "value": verification_uri,
                                    "read_only": True
                                }
                            }
                        },
                        {
                            "id": "user_code",
                            "label": {"en": "User Code"},
                            "field": {
                                "text": {
                                    "value": user_code,
                                    "read_only": True
                                }
                            }
                        },
                        {
                            "id": "waiting_status",
                            "label": {"en": "Status"},
                            "field": {
                                "label": {
                                    "value": {
                                        "en": "Waiting for authentication... This page will automatically continue once you complete authentication."
                                    }
                                }
                            }
                        }
                    ]
                )
            else:
                _LOG.info("Configuration already exists. Completing setup.")
                return SetupComplete()

        if isinstance(request, AbortDriverSetup):
            await self._cleanup_session()
            return

        return SetupError(IntegrationSetupError.OTHER)

    async def _poll_and_complete(self, auth_handler: XboxAuth, device_code: str, interval: int, timeout: int):
        """Background task to poll for tokens and complete setup when received."""
        try:
            _LOG.info("Background polling task started")
            tokens = await auth_handler.poll_for_tokens(device_code, interval, timeout)

            if tokens:
                _LOG.info("Tokens received, saving configuration")
                self.config.tokens = tokens
                await self.config.save(self.api)
                _LOG.info("Setup complete!")
            else:
                _LOG.error("Failed to obtain tokens during polling")

        except Exception as e:
            _LOG.exception(f"Error during background polling: {e}")
        finally:
            await self._cleanup_session()

    async def _cleanup_session(self):
        """Clean up authentication session and cancel polling task."""
        if self.polling_task and not self.polling_task.done():
            _LOG.debug("Cancelling polling task")
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                pass

        if self.auth_session and not self.auth_session.is_closed:
            await self.auth_session.aclose()
            _LOG.debug("Auth session closed")