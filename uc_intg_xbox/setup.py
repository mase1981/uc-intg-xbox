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
                self.config.liveid = request.setup_data.get("liveid", "").strip()

                if not self.config.liveid:
                    return SetupError(IntegrationSetupError.INVALID_INPUT)

                _LOG.info("Live ID captured. Starting OAuth authentication flow.")
                ssl_context = ssl.create_default_context(cafile=certifi.where())
                self.auth_session = httpx.AsyncClient(verify=ssl_context)
                auth_handler = XboxAuth(self.auth_session)
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
                                        "en": "Click the link below to sign in with your Microsoft account.\n"
                                              "After signing in, Microsoft will display your authorization code.\n"
                                              "Copy the code and paste it in the field below."
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
                            "label": {"en": "Step 2: Paste Authorization Code"},
                            "field": {
                                "text": {
                                    "value": ""
                                }
                            }
                        },
                        {
                            "id": "help_text",
                            "label": {"en": "Need Help?"},
                            "field": {
                                "label": {
                                    "value": {
                                        "en": "After signing in, Microsoft will show a page with your authorization code.\n"
                                              "The code is a long string of letters and numbers.\n"
                                              "Copy the entire code and paste it above."
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
            if not self.auth_session:
                return SetupError(IntegrationSetupError.OTHER)

            auth_handler = XboxAuth(self.auth_session)
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