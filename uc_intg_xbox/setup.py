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
    UserDataResponse,
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
        self.auth_session = None

    async def handle_command(self, request):
        if isinstance(request, DriverSetupRequest):
            return await self._handle_driver_setup(request)
        elif isinstance(request, UserDataResponse):
            return await self._handle_user_data_response(request)
        elif isinstance(request, AbortDriverSetup):
            await self._cleanup_session()
            return
        return SetupError(IntegrationSetupError.OTHER)

    async def _handle_driver_setup(self, request):
        self.config.liveid = request.setup_data.get("liveid", "").strip()

        if not self.config.liveid:
            _LOG.error("Live ID is required")
            return SetupError(IntegrationSetupError.INVALID_INPUT)

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.auth_session = httpx.AsyncClient(verify=ssl_context, timeout=30.0)

        auth_handler = XboxAuth(self.auth_session)
        auth_url = auth_handler.generate_auth_url()
        
        return RequestUserInput(
            {"en": "Xbox Authentication"},
            [
                {
                    "id": "auth_url",
                    "label": {"en": "Login URL"},
                    "field": {"text": {"value": auth_url, "read_only": True}},
                },
                {
                    "id": "redirect_url",
                    "label": {"en": "Paste the full redirect URL here"},
                    "field": {"text": {"value": ""}},
                },
            ],
        )

    async def _handle_user_data_response(self, request):
        redirect_url = request.input_values.get("redirect_url", "").strip()
        
        if not self.auth_session:
            return SetupError(IntegrationSetupError.OTHER)
            
        auth_handler = XboxAuth(self.auth_session)
        try:
            tokens = await auth_handler.process_redirect_url(redirect_url)
        finally:
            await self._cleanup_session()
            
        if not tokens:
            return SetupError(IntegrationSetupError.AUTHORIZATION_ERROR)
            
        self.config.tokens = tokens
        await self.config.save(self.api)
        
        return SetupComplete()

    async def _cleanup_session(self):
        if self.auth_session and not self.auth_session.is_closed:
            await self.auth_session.aclose()