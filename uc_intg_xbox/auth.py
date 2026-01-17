"""
Xbox authentication module for Unfolded Circle integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
import asyncio
from urllib.parse import urlparse, parse_qs
import httpx
from pythonxbox.authentication.manager import AuthenticationManager
from pythonxbox.scripts import CLIENT_ID, CLIENT_SECRET

_LOG = logging.getLogger("XBOX_AUTH")
OAUTH2_DESKTOP_REDIRECT_URI = "https://login.live.com/oauth20_desktop.srf"

# Microsoft OAuth2 endpoints for Device Code Flow
DEVICE_CODE_ENDPOINT = "https://login.microsoftonline.com/consumers/oauth2/v2.0/devicecode"
TOKEN_ENDPOINT = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"

# Xbox Live scopes
XBOX_SCOPES = "XboxLive.signin XboxLive.offline_access"

class XboxAuth:
    def __init__(self, session: httpx.AsyncClient):
        self.session = session
        self.auth_mgr = AuthenticationManager(
            session, CLIENT_ID, CLIENT_SECRET, OAUTH2_DESKTOP_REDIRECT_URI
        )
        _LOG.info("XboxAuth initialized.")

    def generate_auth_url(self) -> str:
        return self.auth_mgr.generate_authorization_url()

    async def process_redirect_url(self, redirect_url: str) -> dict | None:
        _LOG.info("Processing redirect URL...")
        try:
            parsed_url = urlparse(redirect_url)
            query_params = parse_qs(parsed_url.query)
            auth_code = query_params.get("code", [None])[0]

            if not auth_code:
                _LOG.error("Authorization code not found in redirect URL.")
                return None

            await self.auth_mgr.request_tokens(auth_code)
            _LOG.info("✅ OAuth2 tokens successfully retrieved.")
            return self.auth_mgr.oauth.model_dump()
        except Exception:
            _LOG.exception("Error during token exchange.")
            return None

    async def request_device_code(self) -> dict | None:
        """
        Request a device code from Microsoft for Device Code Flow authentication.

        Returns dict with:
            - device_code: Code to use for polling
            - user_code: Short code user enters (e.g., "ABC123")
            - verification_uri: URL user visits (e.g., "https://microsoft.com/devicelogin")
            - expires_in: Time in seconds before code expires (typically 900 = 15 min)
            - interval: How often to poll in seconds (typically 5)
            - message: Human-readable message to display to user
        """
        _LOG.info("Requesting device code from Microsoft...")
        try:
            response = await self.session.post(
                DEVICE_CODE_ENDPOINT,
                data={
                    "client_id": CLIENT_ID,
                    "scope": XBOX_SCOPES
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()

            device_code_data = response.json()
            _LOG.info(f"✅ Device code received. User code: {device_code_data.get('user_code')}")
            _LOG.info(f"   Verification URI: {device_code_data.get('verification_uri')}")
            _LOG.info(f"   Expires in: {device_code_data.get('expires_in')} seconds")

            return device_code_data

        except httpx.HTTPStatusError as e:
            _LOG.error(f"HTTP error requesting device code: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            _LOG.exception(f"Error requesting device code: {e}")
            return None

    async def poll_for_tokens(self, device_code: str, interval: int = 5, timeout: int = 900) -> dict | None:
        """
        Poll Microsoft token endpoint until user completes authentication.

        Args:
            device_code: The device_code from request_device_code()
            interval: How often to poll in seconds (from device code response)
            timeout: Maximum time to wait in seconds (from device code response)

        Returns dict with OAuth tokens if successful, None otherwise
        """
        _LOG.info("Starting token polling. Waiting for user to complete authentication...")

        start_time = asyncio.get_event_loop().time()
        poll_count = 0

        while True:
            # Check if we've exceeded timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                _LOG.error(f"⏱️ Token polling timed out after {timeout} seconds")
                return None

            # Wait for the specified interval before polling
            await asyncio.sleep(interval)
            poll_count += 1

            try:
                response = await self.session.post(
                    TOKEN_ENDPOINT,
                    data={
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                        "client_id": CLIENT_ID,
                        "device_code": device_code
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )

                # Check response status
                if response.status_code == 200:
                    tokens = response.json()
                    _LOG.info(f"✅ Authentication successful after {poll_count} polls ({elapsed:.1f} seconds)")
                    _LOG.info(f"   Access token received (expires in {tokens.get('expires_in')} seconds)")

                    # Convert Microsoft tokens to xbox-webapi format
                    return await self._convert_microsoft_tokens_to_xbox(tokens)

                # Parse error response
                error_data = response.json()
                error_code = error_data.get("error", "unknown")

                if error_code == "authorization_pending":
                    # User hasn't completed auth yet, continue polling
                    _LOG.debug(f"Poll #{poll_count}: Still waiting for user authentication...")
                    continue

                elif error_code == "authorization_declined":
                    _LOG.error("❌ User declined authorization")
                    return None

                elif error_code == "expired_token":
                    _LOG.error("⏱️ Device code expired before user completed authentication")
                    return None

                elif error_code == "bad_verification_code":
                    _LOG.error("❌ Invalid device code")
                    return None

                else:
                    _LOG.error(f"❌ Unexpected error during polling: {error_code} - {error_data.get('error_description')}")
                    return None

            except httpx.HTTPStatusError as e:
                _LOG.error(f"HTTP error during token polling: {e.response.status_code} - {e.response.text}")
                return None
            except Exception as e:
                _LOG.exception(f"Error during token polling: {e}")
                return None

    async def _convert_microsoft_tokens_to_xbox(self, microsoft_tokens: dict) -> dict | None:
        """
        Convert Microsoft OAuth tokens to Xbox Live tokens using the xbox-webapi flow.

        Args:
            microsoft_tokens: Raw tokens from Microsoft OAuth (access_token, refresh_token, etc.)

        Returns: Xbox Live tokens in xbox-webapi format
        """
        _LOG.info("Converting Microsoft tokens to Xbox Live tokens...")

        try:
            # The xbox-webapi library needs to exchange Microsoft tokens for Xbox tokens
            # We'll use the AuthenticationManager but manually set the OAuth tokens first

            # Create temporary auth manager with device code redirect (not used but required)
            temp_auth_mgr = AuthenticationManager(
                self.session,
                CLIENT_ID,
                CLIENT_SECRET,
                "urn:ietf:wg:oauth:2.0:oob"  # Out-of-band redirect for device flow
            )

            # Manually construct OAuth response object from Microsoft tokens
            from pythonxbox.authentication.models import OAuth2TokenResponse

            oauth_response = OAuth2TokenResponse(
                token_type=microsoft_tokens.get("token_type", "Bearer"),
                expires_in=microsoft_tokens.get("expires_in", 3600),
                scope=microsoft_tokens.get("scope", XBOX_SCOPES),
                access_token=microsoft_tokens["access_token"],
                refresh_token=microsoft_tokens.get("refresh_token", ""),
                user_id=microsoft_tokens.get("user_id", ""),
                issued=microsoft_tokens.get("issued", 0),
            )

            temp_auth_mgr.oauth = oauth_response

            # Now request Xbox Live tokens using the Microsoft access token
            await temp_auth_mgr.refresh_tokens()

            _LOG.info("✅ Successfully obtained Xbox Live tokens")
            return temp_auth_mgr.oauth.model_dump()

        except Exception as e:
            _LOG.exception(f"Error converting Microsoft tokens to Xbox Live tokens: {e}")
            return None