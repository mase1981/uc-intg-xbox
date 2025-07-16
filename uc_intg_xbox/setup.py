import logging
from ucapi import (
    DriverSetupRequest,
    AbortDriverSetup,
    SetupComplete,
    SetupError,
    IntegrationSetupError,
    RequestUserInput  # We need this to ask for the redirect URL
)
from .config import XboxConfig
from .media_player import XboxMediaPlayer
from .auth import XboxAuth # Import our new auth handler

_LOG = logging.getLogger("XBOX_SETUP")

class XboxSetup:
    def __init__(self, api, config: XboxConfig):
        self.api = api
        self.config = config
        # Create an instance of our auth handler
        self.auth = XboxAuth()
        _LOG.info("✅ SETUP HANDLER INITIALIZED ✅")

    async def handle_command(self, request):
        _LOG.info(f"👉 SETUP HANDLER CALLED! Request type: {type(request)}")

        # This part remains the same: it gets the Live ID
        if isinstance(request, DriverSetupRequest):
            live_id = request.setup_data.get("liveid")
            _LOG.info(f"...Data received from remote form: {live_id}")

            if not live_id:
                _LOG.warning("...Live ID was not found.")
                return SetupError(IntegrationSetupError.OTHER)

            self.config.liveid = live_id.strip()
            # We don't save the config yet, we wait until auth is complete
            _LOG.info(f"...Live ID captured: {self.config.liveid}")

            # NEW STEP: Instead of finishing, we start the auth flow
            try:
                auth_url = await self.auth.generate_auth_url()
                
                # We now ask the user to go to the URL and paste the result
                return RequestUserInput(
                    {"en": "Xbox Authentication"},
                    [
                        {
                            "id": "info",
                            "label": {"en": "Please log in to your Microsoft Account in a browser."},
                            "field": {"label": {"value": {"en": "A new window should have opened. If not, please copy and paste this URL into your browser."}}}
                        },
                        {
                            "id": "auth_url",
                            "label": {"en": "Login URL"},
                            "field": {"text": {"value": auth_url, "read_only": True}}
                        },
                        {
                            "id": "redirect_url",
                            "label": {"en": "Paste the full redirect URL here"},
                            "field": {"text": {"value": ""}}
                        }
                    ]
                )
            except Exception as e:
                _LOG.error(f"Failed to generate auth URL: {e}")
                return SetupError(IntegrationSetupError.OTHER)

        # We will add the handler for the redirect URL in the next step

        if isinstance(request, AbortDriverSetup):
            _LOG.warning("...Setup was aborted by the user or remote.")
            return

        _LOG.warning(f"Unhandled setup request: {request}")
        return SetupError(IntegrationSetupError.OTHER)

    async def create_xbox_entity(self):
        # We will move the logic here after auth is complete
        pass