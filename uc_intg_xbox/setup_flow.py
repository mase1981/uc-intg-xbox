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
        self._choosing_console = False  # waiting for the console picker answer

    def get_manual_entry_form(self, error: str = "") -> RequestUserInput:
        fields = []
        if error:
            fields.append({
                "id": "error",
                "label": {"en": "Error"},
                "field": {"label": {"value": {"en": error}}},
            })
        return RequestUserInput(
            {"en": "Xbox Configuration"},
            fields + [
                {
                    "id": "name",
                    "label": {"en": "Console Name"},
                    "field": {"text": {"value": "Xbox Console"}},
                },
                {
                    "id": "liveid",
                    "label": {"en": "Xbox Live Device ID (Optional)"},
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
                                "en": "Leave the Live Device ID empty to pick your console after signing in. "
                                "To enter it yourself: Xbox Settings > Devices & connections > Remote features.\n\n"
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

        if not client_id:
            self._pending_device_config = None
            return self.get_manual_entry_form("Azure App Client ID is required.")

        self._choosing_console = False
        identifier = _identifier(liveid) if liveid else ""

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

        if self._choosing_console:
            # Console picker answer; the framework already copied "liveid" into the config.
            self._choosing_console = False
            config = self._pending_device_config
            if not config or not config.liveid:
                return SetupError(IntegrationSetupError.NOT_FOUND)
            config.identifier = _identifier(config.liveid)
            return config

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

        client = XboxClient(config.client_id, config.client_secret)
        try:
            try:
                tokens = await client.exchange_code(auth_code)
            except Exception as err:
                _LOG.error("Token exchange failed: %s", err)
                return SetupError(IntegrationSetupError.AUTHORIZATION_ERROR)

            if not tokens:
                return SetupError(IntegrationSetupError.AUTHORIZATION_ERROR)
            config.tokens = tokens

            if config.liveid:
                return config

            try:
                consoles = await client.get_consoles()
            except Exception as err:
                _LOG.error("Could not list consoles: %s", err)
                return SetupError(IntegrationSetupError.CONNECTION_REFUSED)
        finally:
            await client.close()

        if not consoles:
            _LOG.error("No consoles found on this account")
            return SetupError(IntegrationSetupError.NOT_FOUND)

        if len(consoles) == 1:
            config.liveid = consoles[0]["id"]
            config.identifier = _identifier(config.liveid)
            _LOG.info("Using console %s (%s)", consoles[0]["name"], config.liveid)
            return config

        self._choosing_console = True
        return RequestUserInput(
            {"en": "Choose your Xbox"},
            [
                {
                    "id": "liveid",
                    "label": {"en": "Console"},
                    "field": {
                        "dropdown": {
                            "value": consoles[0]["id"],
                            "items": [
                                {"id": console["id"], "label": {"en": f"{console['name']} ({console['id']})"}}
                                for console in consoles
                            ],
                        }
                    },
                },
            ],
        )

    async def _cleanup_oauth(self) -> None:
        if self._oauth_server:
            await self._oauth_server.stop()
            self._oauth_server = None


def _identifier(liveid: str) -> str:
    return f"xbox_{liveid.replace('.', '_')}"


def _extract_code(auth_input: str) -> str:
    _LOG.debug("_extract_code input (length=%d): starts_with_http=%s, has_code=%s",
               len(auth_input), auth_input.startswith("http"), "code=" in auth_input)

    if auth_input.startswith("http") or "code=" in auth_input:
        try:
            if auth_input.startswith("http%3A") or auth_input.startswith("http%3a"):
                auth_input = unquote(auth_input)
                _LOG.debug("URL-decoded input (length=%d)", len(auth_input))

            if auth_input.startswith("http"):
                parsed = urlparse(auth_input)
                params = parse_qs(parsed.query)
                _LOG.debug("Parsed URL: scheme=%s, query_keys=%s, fragment_length=%d",
                           parsed.scheme, list(params.keys()), len(parsed.fragment))

                error = params.get("error", [None])[0]
                if error:
                    error_desc = params.get("error_description", ["Unknown error"])[0]
                    raise ValueError(f"OAuth error: {error} - {unquote(error_desc)}")

                code = params.get("code", [None])[0]
                if code:
                    return code

                if parsed.fragment:
                    frag_params = parse_qs(parsed.fragment)
                    code = frag_params.get("code", [None])[0]
                    if code:
                        _LOG.debug("Found code in URL fragment")
                        return code

            if "code=" in auth_input:
                parts = auth_input.split("code=")
                if len(parts) > 1:
                    code = parts[1].split("&")[0].split("#")[0].split(" ")[0]
                    _LOG.debug("Extracted code via split (length=%d)", len(code))
                    return code
        except ValueError:
            raise
        except Exception as err:
            _LOG.warning("_extract_code parse error: %s", err)

    _LOG.debug("_extract_code: returning raw input as code")
    return auth_input
