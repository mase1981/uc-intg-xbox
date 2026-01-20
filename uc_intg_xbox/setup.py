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
        self.console_count: int = 0
        self.consoles_data: list = []

    async def handle_command(self, request):
        # Handle initial setup request - Page 1: Get console count and Azure credentials
        if isinstance(request, DriverSetupRequest):
            if request.reconfigure or not self.config.tokens:
                # Capture Azure App credentials and console count
                self.config.client_id = request.setup_data.get("client_id", "").strip()
                self.config.client_secret = request.setup_data.get("client_secret", "").strip()

                if not self.config.client_id:
                    _LOG.error("Azure App Client ID is required.")
                    return SetupError(IntegrationSetupError.INVALID_INPUT)

                # Client secret is optional - used for Web apps, not needed for Mobile/Desktop apps
                if self.config.client_secret:
                    _LOG.info("Client secret provided - using Web app (confidential client) flow")
                    # Warn about special characters that may cause issues
                    problematic_chars = ['+', '~', '/']
                    found_chars = [c for c in problematic_chars if c in self.config.client_secret]
                    if found_chars:
                        _LOG.warning(
                            f"Client secret contains special characters {found_chars} that may cause "
                            "authentication failures. If setup fails with 'unauthorized_client' error, "
                            "try using Mobile/Desktop app platform (no secret required). "
                            "See AZURE_SETUP_GUIDE.md for details."
                        )
                else:
                    _LOG.info("No client secret provided - using Mobile/Desktop app (public client) flow")

                console_count_value = request.setup_data.get("console_count")
                if console_count_value is None:
                    _LOG.error("console_count field missing from setup_data")
                    return SetupError(IntegrationSetupError.OTHER)

                try:
                    self.console_count = int(console_count_value)
                except (ValueError, TypeError):
                    _LOG.error(f"Invalid console_count value: {console_count_value}")
                    return SetupError(IntegrationSetupError.OTHER)

                if self.console_count < 1 or self.console_count > 10:
                    _LOG.error(f"Console count out of range: {self.console_count}")
                    return SetupError(IntegrationSetupError.OTHER)

                _LOG.info(f"User requested {self.console_count} console(s)")
                _LOG.info("Credentials captured. Proceeding to console configuration.")

                # Page 2: Show dynamic form for console details
                return self._build_console_input_form()
            else:
                _LOG.info("Configuration already exists. Completing setup.")
                return SetupComplete()

        # Handle OAuth completion - Page 3: Exchange code for tokens and save config
        # Check this BEFORE Page 2 to avoid false positives when auth_url is present
        if hasattr(request, 'input_values') and "auth_url" in request.input_values:
            _LOG.info("Processing OAuth authentication page")

            if not self.auth_handler:
                _LOG.error("No auth handler available")
                await self._cleanup_session()
                return SetupError(IntegrationSetupError.OTHER)

            manual_code = request.input_values.get("manual_code", "").strip()

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

            # Add all configured consoles
            _LOG.info(f"Adding {len(self.consoles_data)} console(s) to configuration...")
            for console_data in self.consoles_data:
                self.config.add_console(
                    liveid=console_data["liveid"],
                    name=console_data["name"],
                    enabled=True
                )
                _LOG.info(f"Added console: {console_data['name']}")

            await self.config.save(self.api)
            _LOG.info("Setup completed successfully!")
            return SetupComplete()

        # Handle console details input - Page 2: Collect console names and Live IDs
        # Check this AFTER Page 3 OAuth handler
        if hasattr(request, 'input_values') and any(f"console_0_name" in key or f"console_0_liveid" in key for key in request.input_values.keys()):
            _LOG.info("Received console configuration data")

            self.consoles_data = []
            for i in range(self.console_count):
                console_name = request.input_values.get(f"console_{i}_name", f"Xbox Console {i+1}").strip()
                console_liveid = request.input_values.get(f"console_{i}_liveid", "").strip()

                if not console_name or not console_liveid:
                    _LOG.error(f"Console {i+1}: Missing name or Live ID")
                    return SetupError(IntegrationSetupError.OTHER)

                self.consoles_data.append({
                    "name": console_name,
                    "liveid": console_liveid
                })
                _LOG.info(f"Console {i+1}: {console_name} (Live ID: {console_liveid[:8]}...)")

            # Page 3: Start OAuth authentication flow
            _LOG.info("Console details captured. Starting OAuth authentication flow with local callback server.")

            # Clean up any existing session/handler (in case of retry)
            await self._cleanup_session()

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

        if isinstance(request, AbortDriverSetup):
            await self._cleanup_session()
            return

        return SetupError(IntegrationSetupError.OTHER)

    def _build_console_input_form(self) -> RequestUserInput:
        """Build dynamic form for console details based on count."""
        settings = []

        for i in range(self.console_count):
            settings.extend([
                {
                    "id": f"console_{i}_name",
                    "label": {
                        "en": f"Console {i+1} Name"
                    },
                    "field": {
                        "text": {
                            "value": f"Xbox Console {i+1}"
                        }
                    }
                },
                {
                    "id": f"console_{i}_liveid",
                    "label": {
                        "en": f"Console {i+1} Xbox Live Device ID"
                    },
                    "field": {
                        "text": {
                            "value": ""
                        }
                    }
                }
            ])

        return RequestUserInput(
            title={"en": "Configure Xbox Consoles"},
            settings=settings
        )

    async def _cleanup_session(self):
        """Clean up authentication session and OAuth server."""
        # Stop OAuth callback server if running
        if self.auth_handler and self.auth_handler.callback_server:
            try:
                await self.auth_handler.callback_server.stop()
                _LOG.debug("OAuth callback server stopped during cleanup")
            except Exception as e:
                _LOG.warning(f"Error stopping OAuth server during cleanup: {e}")

        # Close HTTP session
        if self.auth_session and not self.auth_session.is_closed:
            await self.auth_session.aclose()
            _LOG.debug("Auth session closed")

        # Clear auth handler reference
        self.auth_handler = None