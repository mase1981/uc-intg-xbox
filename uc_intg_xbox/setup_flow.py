"""
Xbox setup flow with OAuth authentication.

Every mistake a user can make here (wrong paste, expired code, a client secret
that is missing, not needed or wrong, a Device ID that is not on the account)
keeps the setup open with a message, instead of aborting it.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import json
import logging
import re
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from ucapi import (
    AbortDriverSetup,
    DriverSetupRequest,
    IntegrationSetupError,
    RequestUserInput,
    SetupError,
)
from ucapi_framework import BaseSetupFlow

from uc_intg_xbox.client import XboxClient
from uc_intg_xbox.config import XboxConfig
from uc_intg_xbox.oauth_server import OAuthCallbackServer

_LOG = logging.getLogger(__name__)

# How long Submit waits for the automatic callback before asking for the pasted URL.
CALLBACK_WAIT = 20
DEFAULT_NAME = "Xbox Console"
GUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


class XboxSetupFlow(BaseSetupFlow[XboxConfig]):
    """Xbox setup flow with multi-step OAuth authentication."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._oauth_server: OAuthCallbackServer | None = None
        self._auth_url = ""
        self._last_paste = ""
        self._choosing_console = False  # waiting for the console picker answer

    async def handle_driver_setup(self, msg):
        # The setup flow instance is reused for every setup. A cancelled or failed
        # setup must not leave a half-finished config or the callback server behind,
        # or the next setup is routed into the sign-in step and hangs.
        if isinstance(msg, (DriverSetupRequest, AbortDriverSetup)):
            await self._reset()
        return await super().handle_driver_setup(msg)

    async def _reset(self) -> None:
        await self._cleanup_oauth()
        self._pending_device_config = None
        self._choosing_console = False
        self._auth_url = ""
        self._last_paste = ""

    # ------------------------------------------------------------------
    # Screens
    # ------------------------------------------------------------------
    def get_manual_entry_form(self, error: str = "", values: dict | None = None) -> RequestUserInput:
        if values is None:
            # Updating an existing console: start from what is saved.
            current = self.selected_config_entry
            values = {
                "name": current.name,
                "liveid": current.liveid,
                "client_id": current.client_id,
                "client_secret": current.client_secret,
            } if current else {}
        return RequestUserInput(
            {"en": "Xbox Configuration"},
            _error_field(error) + [
                {
                    "id": "name",
                    "label": {"en": "Console Name"},
                    "field": {"text": {"value": values.get("name") or DEFAULT_NAME}},
                },
                {
                    "id": "liveid",
                    "label": {"en": "Xbox Live Device ID (Optional)"},
                    "field": {"text": {"value": values.get("liveid", "")}},
                },
                {
                    "id": "client_id",
                    "label": {"en": "Azure App Client ID"},
                    "field": {"text": {"value": values.get("client_id", "")}},
                },
                {
                    "id": "client_secret",
                    "label": {"en": "Azure App Client Secret (Optional)"},
                    "field": {"password": {"value": values.get("client_secret", "")}},
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

    def _auth_screen(self, error: str = "", ask_secret: bool = False) -> RequestUserInput:
        fields = _error_field(error) + [
            {
                "id": "instructions",
                "label": {"en": "Step 1: Authenticate"},
                "field": {
                    "label": {
                        "value": {
                            "en": "Open the Authorization URL below in a browser and sign in with your Microsoft account.\n"
                            "After signing in, the browser goes to a page starting with http://localhost:8765/callback?code= "
                            "that will not load. Copy that full address (or just the code) and paste it below."
                        }
                    }
                },
            },
            {
                "id": "auth_url",
                "label": {"en": "Authorization URL"},
                "field": {"text": {"value": self._auth_url, "read_only": True}},
            },
        ]
        if ask_secret:
            fields.append({
                "id": "client_secret",
                "label": {"en": "Azure App Client Secret (the secret Value, not the Secret ID)"},
                "field": {"password": {"value": ""}},
            })
        fields += [
            {
                "id": "manual_code",
                "label": {"en": "Step 2: Paste the URL or code after signing in"},
                # After a client secret problem the code was not used yet; keep it.
                "field": {"text": {"value": self._last_paste if ask_secret else ""}},
            },
            {
                "id": "help_text",
                "label": {"en": "Instructions"},
                "field": {
                    "label": {
                        "value": {
                            "en": "Paste the address you land on AFTER signing in (it contains code=), "
                            "or only the code. Not the Authorization URL above.\n"
                            "If Microsoft shows an error page instead, check that the redirect URI "
                            "http://localhost:8765/callback is added to your Azure app."
                        }
                    }
                },
            },
        ]
        return RequestUserInput({"en": "Xbox Authentication"}, fields)

    def _console_picker(self, consoles: list[dict], error: str = "") -> RequestUserInput:
        return RequestUserInput(
            {"en": "Choose your Xbox"},
            _error_field(error) + [
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

    # ------------------------------------------------------------------
    # Step 1: console details
    # ------------------------------------------------------------------
    async def query_device(
        self, input_values: dict[str, Any]
    ) -> XboxConfig | RequestUserInput:
        name = (input_values.get("name") or "").strip() or DEFAULT_NAME
        liveid = _no_spaces(input_values.get("liveid"))
        client_id = _no_spaces(input_values.get("client_id"))
        client_secret = (input_values.get("client_secret") or "").strip()
        entered = {"name": name, "liveid": liveid, "client_id": client_id, "client_secret": client_secret}

        if not client_id:
            self._pending_device_config = None
            return self.get_manual_entry_form("Azure App Client ID is required.", entered)
        if not GUID.match(client_id):
            self._pending_device_config = None
            return self.get_manual_entry_form(
                "The Client ID looks wrong. Use the Application (client) ID from your Azure app's Overview page "
                "(format 00000000-0000-0000-0000-000000000000).",
                entered,
            )

        self._choosing_console = False
        self._last_paste = ""
        self._pending_device_config = XboxConfig(
            identifier=_identifier(liveid) if liveid else "",
            name=name,
            liveid=liveid,
            client_id=client_id,
            client_secret=client_secret,
        )

        self._auth_url = XboxClient(client_id, client_secret).generate_auth_url()

        # Optional: catches the callback when the browser can reach the Remote on 8765.
        # Pasting works without it, so a busy port must not stop the setup.
        await self._cleanup_oauth()
        server = OAuthCallbackServer()
        try:
            await server.start()
            self._oauth_server = server
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.warning("OAuth callback server not started (paste the URL instead): %s", err)
            await server.stop()

        return self._auth_screen()

    # ------------------------------------------------------------------
    # Step 2: sign-in, step 3: console picker (only when needed)
    # ------------------------------------------------------------------
    async def handle_additional_configuration_response(self, msg) -> XboxConfig | None:
        input_values = msg.input_values if hasattr(msg, "input_values") else {}
        config = self._pending_device_config
        if not config:
            await self._cleanup_oauth()
            return SetupError(IntegrationSetupError.OTHER)

        if self._choosing_console:
            # Console picker answer; the framework already copied "liveid" into the config.
            self._choosing_console = False
            if not config.liveid:
                return SetupError(IntegrationSetupError.NOT_FOUND)
            config.identifier = self._identifier_for(config.liveid)
            return config

        # The secret field is only on the screen after a secret problem; the framework
        # copied it into the config already. Normalise it like the first screen.
        config.client_secret = (config.client_secret or "").strip()

        paste = _clean_paste(input_values.get("manual_code"))
        auth_code = None
        if paste:
            self._last_paste = paste
            if "oauth20_authorize" in paste:
                return self._auth_screen(
                    "That is the Authorization URL. Open it, sign in, then paste the address "
                    "you land on (it starts with http://localhost:8765/callback?code=)."
                )
            if "error=" in paste and "code=" not in paste:
                query = parse_qs(paste.split("?", 1)[-1])
                reason = query.get("error_description", query.get("error", ["unknown"]))[0]
                return self._auth_screen(f"Microsoft returned an error: {_short(reason)}. Open the URL and sign in again.")
            try:
                auth_code = _extract_code(paste)
            except ValueError as err:
                _LOG.error("OAuth error: %s", err)
                return self._auth_screen(f"{err}. Open the Authorization URL and sign in again.")
            if not auth_code or (paste.lower().startswith("http") and "code=" not in paste):
                return self._auth_screen(
                    "No code found in what you pasted. Paste the full address you land on after signing in."
                )
        elif self._oauth_server:
            auth_code = await self._oauth_server.wait_for_code(timeout=CALLBACK_WAIT)

        if not auth_code:
            _LOG.warning("No authorization code received yet")
            return self._auth_screen("No sign-in received. Paste the address you land on after signing in.")

        client, tokens, problem = await self._exchange(config, auth_code)
        if not tokens:
            return problem
        try:
            await self._cleanup_oauth()
            config.tokens = tokens
            try:
                consoles = await client.get_consoles()
            except Exception as err:  # pylint: disable=broad-exception-caught
                _LOG.warning("Could not list consoles: %s", err)
                consoles = None
        finally:
            await client.close()

        if config.liveid:
            return self._confirm_liveid(config, consoles)

        if consoles is None:
            return SetupError(IntegrationSetupError.CONNECTION_REFUSED)
        if not consoles:
            _LOG.error("No consoles found on this account")
            return SetupError(IntegrationSetupError.NOT_FOUND)
        if len(consoles) == 1:
            config.liveid = consoles[0]["id"]
            config.identifier = self._identifier_for(config.liveid)
            _LOG.info("Using console %s (%s)", consoles[0]["name"], config.liveid)
            return config
        self._choosing_console = True
        return self._console_picker(consoles)

    def _confirm_liveid(self, config: XboxConfig, consoles: list[dict] | None):
        """A Device ID was entered: match it to the account, as typed if the list is unavailable."""
        if consoles:
            match = next((c for c in consoles if c["id"].lower() == config.liveid.lower()), None)
            if match:
                config.liveid = match["id"]  # the account's spelling
            else:
                _LOG.warning("Device ID %s is not on this account", config.liveid)
                self._choosing_console = True
                return self._console_picker(
                    consoles,
                    f"Device ID {config.liveid} was not found on this Microsoft account. Choose your console.",
                )
        else:
            _LOG.warning("Console list unavailable, using the Device ID as entered")
        config.identifier = self._identifier_for(config.liveid)
        return config

    def _identifier_for(self, liveid: str) -> str:
        """Keep the saved identifier (and so the entity IDs) when updating the same console."""
        current = self.selected_config_entry
        if current and current.liveid and current.liveid.lower() == liveid.lower():
            return current.identifier
        return _identifier(liveid)

    async def _exchange(self, config: XboxConfig, code: str):
        """Trade the code for tokens. Returns (client, tokens, screen to show on failure)."""
        client = XboxClient(config.client_id, config.client_secret)
        tokens, error = await _try_exchange(client, code)
        if tokens:
            return client, tokens, None
        await client.close()
        lower = error.lower()

        if "invalid_grant" in lower:
            return None, None, self._auth_screen(
                "Microsoft did not accept this code (it expires after a few minutes and works only once). "
                "Open the Authorization URL again, sign in, and paste the new address."
            )

        if config.client_secret:
            # A secret on a Mobile/Desktop app is rejected before the code is used: try without it.
            retry = XboxClient(config.client_id, "")
            tokens, retry_error = await _try_exchange(retry, code)
            if tokens:
                _LOG.info("Azure app does not use a client secret; continuing without it")
                config.client_secret = ""
                return retry, tokens, None
            await retry.close()
            if "secret" in lower or "invalid_client" in lower:
                return None, None, self._auth_screen(
                    f"Microsoft rejected the client secret ({_short(error)}). Paste the secret Value "
                    "(not the Secret ID) from Azure > Certificates & secrets, or clear it for a Mobile/Desktop app.",
                    ask_secret=True,
                )
            error = retry_error or error
            lower = error.lower()

        elif "secret" in lower or "client_assertion" in lower:
            return None, None, self._auth_screen(
                "This Azure app is a Web app and needs its client secret. Enter the secret Value below.",
                ask_secret=True,
            )

        if "invalid_client" in lower or "unauthorized_client" in lower:
            return None, None, self._auth_screen(
                f"Microsoft rejected the app ({_short(error)}). Check the Client ID and that the Azure app "
                "allows personal Microsoft accounts."
            )
        return None, None, self._auth_screen(f"Sign-in failed ({_short(error)}). Open the URL and try again.")

    async def _cleanup_oauth(self) -> None:
        if self._oauth_server:
            server, self._oauth_server = self._oauth_server, None
            await server.stop()


async def _try_exchange(client: XboxClient, code: str) -> tuple[dict | None, str]:
    """(tokens, "") or (None, Microsoft's error text)."""
    try:
        tokens = await client.exchange_code(code)
        return (tokens, "") if tokens else (None, "no tokens returned")
    except Exception as err:  # pylint: disable=broad-exception-caught
        response = getattr(err, "response", None)
        text = getattr(response, "text", "") if response is not None else ""
        _LOG.error("Token exchange failed: %s %s", err, text)
        return None, text or str(err)


def _short(error: str) -> str:
    """Microsoft's error description, without the trace and correlation ids."""
    try:
        data = json.loads(error)
        text = data.get("error_description") or data.get("error") or error
    except (ValueError, AttributeError):
        text = error
    return text.split("\r")[0].split("\n")[0].split(" Trace ID")[0][:160]


def _no_spaces(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or ""))


def _clean_paste(value: Any) -> str:
    """Remove line breaks and spaces (phone copy), wrapping quotes or brackets, URL encoding."""
    text = _no_spaces(value).strip("\"'<>()[]")
    if "%3a" in text.lower() or "%3d" in text.lower():
        text = unquote(text)
    return text


def _error_field(error: str) -> list[dict]:
    if not error:
        return []
    return [{
        "id": "error",
        "label": {"en": "Error"},
        "field": {"label": {"value": {"en": error}}},
    }]


def _identifier(liveid: str) -> str:
    return f"xbox_{liveid.replace('.', '_')}"


def _extract_code(auth_input: str) -> str:
    _LOG.debug("_extract_code input (length=%d): starts_with_http=%s, has_code=%s",
               len(auth_input), auth_input.startswith("http"), "code=" in auth_input)

    if auth_input.lower().startswith("http") or "code=" in auth_input or "code%3d" in auth_input.lower():
        try:
            if auth_input.lower().startswith("http%3a") or "code%3d" in auth_input.lower():
                auth_input = unquote(auth_input)
                _LOG.debug("URL-decoded input (length=%d)", len(auth_input))

            if auth_input.lower().startswith("http"):
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
