"""
Xbox setup flow with OAuth authentication.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from ucapi import RequestUserInput, SetupError, IntegrationSetupError
from ucapi_framework import BaseSetupFlow

from uc_intg_xbox.client import XboxClient
from uc_intg_xbox.config import XboxConfig
from uc_intg_xbox.oauth_server import OAuthCallbackServer

_LOG = logging.getLogger(__name__)


class XboxSetupFlow(BaseSetupFlow[XboxConfig]):
    """Xbox setup flow with multi-step OAuth authentication."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._oauth_server: OAuthCallbackServer | None = None

    def get_manual_entry_form(self) -> RequestUserInput:
        return RequestUserInput(
            {"en": "Xbox Configuration"},
            [
                {
                    "id": "name",
                    "label": {"en": "Console Name"},
                    "field": {"text": {"value": "Xbox Console"}},
                },
                {
                    "id": "liveid",
                    "label": {"en": "Xbox Live Device ID"},
                    "field": {"text": {"value": ""}},
                },
                {
                    "id": "client_id",
                    "label": {"en": "Azure App Client ID"},
                    "field": {"text": {"value": ""}},
                },
                {
                    "id": "client_secret",
                    "label": {"en": "Azure App Client Secret (Optional)"},
                    "field": {"password": {"value": ""}},
                },
                {
                    "id": "help",
                    "label": {"en": "Instructions"},
                    "field": {
                        "label": {
                            "value": {
                                "en": "Find your Xbox Live Device ID in: Xbox Settings > Devices & connections > Remote features.\n\n"
                                "You need an Azure App Registration with Xbox Live API permissions.\n"
                                "Client Secret is optional (required for Web apps, not needed for Mobile/Desktop apps)."
                            }
                        }
                    },
                },
            ],
        )

    async def query_device(
        self, input_values: dict[str, Any]
    ) -> XboxConfig | RequestUserInput:
        name = input_values.get("name", "Xbox Console").strip()
        liveid = input_values.get("liveid", "").strip()
        client_id = input_values.get("client_id", "").strip()
        client_secret = input_values.get("client_secret", "").strip()

        if not liveid:
            raise ValueError("Xbox Live Device ID is required")
        if not client_id:
            raise ValueError("Azure App Client ID is required")

        identifier = f"xbox_{liveid.replace('.', '_')}"

        self._pending_device_config = XboxConfig(
            identifier=identifier,
            name=name,
            liveid=liveid,
            client_id=client_id,
            client_secret=client_secret,
        )

        temp_client = XboxClient(client_id, client_secret)
        auth_url = temp_client.generate_auth_url()

        self._oauth_server = OAuthCallbackServer()
        await self._oauth_server.start()

        return RequestUserInput(
            {"en": "Xbox Authentication"},
            [
                {
                    "id": "instructions",
                    "label": {"en": "Step 1: Authenticate"},
                    "field": {
                        "label": {
                            "value": {
                                "en": "Open the Authorization URL below in a browser and sign in with your Microsoft account.\n"
                                "The integration will try to capture the callback automatically.\n"
                                "If automatic callback doesn't work, paste the redirect URL or code below."
                            }
                        }
                    },
                },
                {
                    "id": "auth_url",
                    "label": {"en": "Authorization URL"},
                    "field": {"text": {"value": auth_url, "read_only": True}},
                },
                {
                    "id": "manual_code",
                    "label": {"en": "Step 2: Manual Code (Optional)"},
                    "field": {"text": {"value": ""}},
                },
                {
                    "id": "help_text",
                    "label": {"en": "Instructions"},
                    "field": {
                        "label": {
                            "value": {
                                "en": "AUTOMATIC: Click the URL, sign in, and click Submit.\n"
                                "MANUAL: If redirect fails, copy the URL from your browser and paste it in Manual Code.\n"
                                "Server listening on port 8765. Timeout: 5 minutes."
                            }
                        }
                    },
                },
            ],
        )

    async def handle_additional_configuration_response(self, msg) -> XboxConfig | None:
        input_values = msg.input_values if hasattr(msg, "input_values") else {}
        manual_code = input_values.get("manual_code", "").strip()
        auth_code = None

        try:
            if manual_code:
                auth_code = _extract_code(manual_code)
                _LOG.debug("Extracted auth code from manual input (length=%d)", len(auth_code) if auth_code else 0)
            elif self._oauth_server:
                auth_code = await self._oauth_server.wait_for_code(timeout=300)
        except ValueError as err:
            _LOG.error("OAuth error: %s", err)
            await self._cleanup_oauth()
            return SetupError(IntegrationSetupError.AUTHORIZATION_ERROR)
        finally:
            await self._cleanup_oauth()

        if not auth_code:
            _LOG.error("No authorization code received")
            return SetupError(IntegrationSetupError.AUTHORIZATION_ERROR)

        config = self._pending_device_config
        if not config:
            return SetupError(IntegrationSetupError.OTHER)

        try:
            client = XboxClient(config.client_id, config.client_secret)
            tokens = await client.exchange_code(auth_code)
            await client.close()
        except Exception as err:
            _LOG.error("Token exchange failed: %s", err)
            return SetupError(IntegrationSetupError.AUTHORIZATION_ERROR)

        if not tokens:
            return SetupError(IntegrationSetupError.AUTHORIZATION_ERROR)

        config.tokens = tokens
        return config

    async def _cleanup_oauth(self) -> None:
        if self._oauth_server:
            await self._oauth_server.stop()
            self._oauth_server = None


def _extract_code(auth_input: str) -> str:
    if auth_input.startswith("http") or "code=" in auth_input:
        try:
            if auth_input.startswith("http%3A"):
                auth_input = unquote(auth_input)

            if auth_input.startswith("http"):
                parsed = urlparse(auth_input)
                params = parse_qs(parsed.query)

                error = params.get("error", [None])[0]
                if error:
                    error_desc = params.get("error_description", ["Unknown error"])[0]
                    raise ValueError(f"OAuth error: {error} - {unquote(error_desc)}")

                code = params.get("code", [None])[0]
                if code:
                    return code

            elif "code=" in auth_input:
                parts = auth_input.split("code=")
                if len(parts) > 1:
                    return parts[1].split("&")[0].split("#")[0]
        except ValueError:
            raise
        except Exception:
            pass

    return auth_input
