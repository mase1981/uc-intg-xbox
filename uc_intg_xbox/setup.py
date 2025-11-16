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
        _LOG.info(f"Setup received request type: {type(request)}")
        _LOG.info(f"Setup request attributes: {dir(request)}")
        
        if isinstance(request, DriverSetupRequest):
            if request.reconfigure or not self.config.tokens:
                self.config.liveid = request.setup_data.get("liveid", "").strip()

                if not self.config.liveid:
                    _LOG.error("Live ID is empty or invalid")
                    return SetupError(IntegrationSetupError.INVALID_INPUT)

                _LOG.info("Live ID captured. Starting new auth flow.")
                ssl_context = ssl.create_default_context(cafile=certifi.where())
                self.auth_session = httpx.AsyncClient(verify=ssl_context)
                auth_handler = XboxAuth(self.auth_session)
                auth_url = auth_handler.generate_auth_url()

                return RequestUserInput(
                    {"en": "Xbox Authentication"},
                    [
                        {"id": "auth_url", "label": {"en": "Login URL"}, "field": {"text": {"value": auth_url, "read_only": True}}},
                        {"id": "redirect_url", "label": {"en": "Paste the full redirect URL here"}, "field": {"text": {"value": ""}}},
                    ]
                )
            else:
                _LOG.info("Configuration already exists. Completing setup.")
                return SetupComplete()

        if hasattr(request, 'input_values'):
            _LOG.info(f"Request has input_values: {request.input_values}")
            if "redirect_url" in request.input_values:
                redirect_url = request.input_values.get("redirect_url", "").strip()
                _LOG.info(f"Processing redirect URL (first 50 chars): {redirect_url[:50]}")
                
                if not self.auth_session:
                    _LOG.error("Auth session is None")
                    return SetupError(IntegrationSetupError.OTHER)

                auth_handler = XboxAuth(self.auth_session)
                try:
                    tokens = await auth_handler.process_redirect_url(redirect_url)
                    _LOG.info(f"Tokens received: {bool(tokens)}")
                except Exception as e:
                    _LOG.exception(f"Exception during token processing: {e}")
                    tokens = None
                finally:
                    await self._cleanup_session()

                if not tokens:
                    _LOG.error("No tokens received from authentication")
                    return SetupError(IntegrationSetupError.AUTHENTICATION_FAILED)

                self.config.tokens = tokens
                await self.config.save(self.api)
                _LOG.info("Tokens saved successfully")
                return SetupComplete()

        if isinstance(request, AbortDriverSetup):
            _LOG.info("Setup aborted by user")
            await self._cleanup_session()
            return

        _LOG.error(f"Unhandled request type: {type(request)}")
        return SetupError(IntegrationSetupError.OTHER)

    async def _cleanup_session(self):
        if self.auth_session and not self.auth_session.is_closed:
            await self.auth_session.aclose()
            _LOG.info("Auth session closed")