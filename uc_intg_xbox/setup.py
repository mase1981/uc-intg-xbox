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
        self.auth_handler: XboxAuth | None = None

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

                _LOG.info("Credentials captured. Starting OAuth authentication flow with local callback server.")
                ssl_context = ssl.create_default_context(cafile=certifi.where())
                self.auth_session = httpx.AsyncClient(verify=ssl_context)
                self.auth_handler = XboxAuth(self.auth_session, self.config.client_id, self.config.client_secret)

                # Start the OAuth flow and get the auth URL
                result = await self.auth_handler.authenticate_with_oauth()
                if not result or "auth_url" not in result:
                    _LOG.error("Failed to start OAuth flow")
                    await self._cleanup_session()
                    return SetupError(IntegrationSetupError.OTHER)

                auth_url = result["auth_url"]

                return RequestUserInput(
                    {"en": "Xbox Authentication"},
                    [
                        {
                            "id": "instructions",
                            "label": {"en": "Step 1: Authenticate"},
                            "field": {
                                "label": {
                                    "value": {
                                        "en": "Click the Authorization URL below to sign in with your Microsoft account.\n"
                                              "The integration will try to receive the callback automatically.\n"
                                              "If automatic callback doesn't work, you can manually paste the code."
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
                            "id": "manual_code",
                            "label": {"en": "Step 2: Manual Code (Optional)"},
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
                                        "en": "AUTOMATIC (Recommended):\n"
                                              "1. Click the Authorization URL above\n"
                                              "2. Sign in with your Microsoft account\n"
                                              "3. If redirected successfully, just click Submit below\n\n"
                                              "MANUAL (Fallback):\n"
                                              "1. If redirect fails, copy the URL from your browser address bar\n"
                                              "2. Paste it in the 'Manual Code' field (or just the code= part)\n"
                                              "3. Click Submit\n\n"
                                              "Server listening on port 8765. Timeout: 5 minutes."
                                    }
                                }
                            }
                        }
                    ]
                )
            else:
                _LOG.info("Configuration already exists. Completing setup.")
                return SetupComplete()

        if hasattr(request, 'input_values') and ("manual_code" in request.input_values or "confirm" in request.input_values):
            if not self.auth_handler:
                _LOG.error("No auth handler available")
                await self._cleanup_session()
                return SetupError(IntegrationSetupError.OTHER)

            manual_code = request.input_values.get("manual_code", "").strip() if hasattr(request, 'input_values') else ""

            try:
                if manual_code:
                    # Manual code provided - use it directly
                    _LOG.info(f"Manual code provided (length: {len(manual_code)}), processing...")
                    tokens = await self.auth_handler.process_manual_code(manual_code)
                else:
                    # No manual code - wait for automatic callback
                    _LOG.info("No manual code provided, waiting for OAuth callback from local server...")
                    tokens = await self.auth_handler.wait_for_auth_completion(timeout=300)
            except Exception as e:
                _LOG.exception(f"Error during OAuth completion: {e}")
                tokens = None
            finally:
                await self._cleanup_session()

            if not tokens:
                _LOG.error("Failed to receive OAuth tokens")
                return SetupError(IntegrationSetupError.AUTHENTICATION_FAILED)

            self.config.tokens = tokens
            await self.config.save(self.api)
            _LOG.info("OAuth authentication completed successfully!")
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