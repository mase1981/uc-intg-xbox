"""
Xbox setup module for Unfolded Circle integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
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

    async def handle_command(self, request):
        if isinstance(request, DriverSetupRequest):
            if request.reconfigure or not self.config.tokens:
                # Capture Azure App credentials
                self.config.client_id = request.setup_data.get("client_id", "").strip()
                self.config.client_secret = request.setup_data.get("client_secret", "").strip()
                self.config.liveid = request.setup_data.get("liveid", "").strip()

                if not self.config.client_id or not self.config.client_secret:
                    _LOG.error("Azure App credentials missing.")
                    return SetupError(IntegrationSetupError.INVALID_INPUT)

                if not self.config.liveid:
                    _LOG.error("Xbox Live Device ID missing.")
                    return SetupError(IntegrationSetupError.INVALID_INPUT)

                _LOG.info("Credentials captured. Starting OAuth authentication flow.")
                ssl_context = ssl.create_default_context(cafile=certifi.where())
                self.auth_session = httpx.AsyncClient(verify=ssl_context)
                auth_handler = XboxAuth(self.auth_session, self.config.client_id, self.config.client_secret)
                auth_url = auth_handler.generate_auth_url()

                return RequestUserInput(
                    {"en": "Xbox Authentication"},
                    [
                        {
                            "id": "instructions",
                            "label": {"en": "Step 1: Authenticate"},
                            "field": {
                                "label": {
                                    "value": {
                                        "en": "IMPORTANT: Right-click the link below and select 'Copy link address'.\n"
                                              "Paste it into a NEW browser tab (do NOT click directly).\n"
                                              "This prevents the browser from closing after authentication."
                                    }
                                }
                            }
                        },
                        {
                            "id": "auth_url",
                            "label": {"en": "Authorization URL"},
                            "field": {
                                "text": {
                                    "value": auth_url,
                                    "read_only": True
                                }
                            }
                        },
                        {
                            "id": "auth_code",
                            "label": {"en": "Step 2: Paste URL or Code"},
                            "field": {
                                "text": {
                                    "value": ""
                                }
                            }
                        },
                        {
                            "id": "help_text",
                            "label": {"en": "Instructions"},
                            "field": {
                                "label": {
                                    "value": {
                                        "en": "1. Copy the Authorization URL above\n"
                                              "2. Paste it into a NEW browser tab\n"
                                              "3. Sign in with your Microsoft account\n"
                                              "4. After signing in, QUICKLY copy the URL from the address bar\n"
                                              "   It will look like: http://localhost/?code=M.R3_BAY.abc123...\n"
                                              "5. Paste the ENTIRE URL in Step 2 above\n\n"
                                              "Note: The page may be blank or show an error - this is normal!\n"
                                              "The important part is the URL in the address bar."
                                    }
                                }
                            }
                        }
                    ]
                )
            else:
                _LOG.info("Configuration already exists. Completing setup.")
                return SetupComplete()

        if hasattr(request, 'input_values') and "auth_code" in request.input_values:
            auth_code = request.input_values.get("auth_code", "").strip()
            if not self.auth_session or not self.config.client_id or not self.config.client_secret:
                return SetupError(IntegrationSetupError.OTHER)

            auth_handler = XboxAuth(self.auth_session, self.config.client_id, self.config.client_secret)
            try:
                tokens = await auth_handler.process_auth_code(auth_code)
            finally:
                await self._cleanup_session()

            if not tokens:
                return SetupError(IntegrationSetupError.AUTHENTICATION_FAILED)

            self.config.tokens = tokens
            await self.config.save(self.api)
            return SetupComplete()

        if isinstance(request, AbortDriverSetup):
            await self._cleanup_session()
            return

        return SetupError(IntegrationSetupError.OTHER)

    async def _cleanup_session(self):
        """Clean up authentication session."""
        if self.auth_session and not self.auth_session.is_closed:
            await self.auth_session.aclose()
            _LOG.debug("Auth session closed")