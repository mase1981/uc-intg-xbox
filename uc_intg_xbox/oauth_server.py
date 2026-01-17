"""
OAuth callback server for Xbox authentication.

This module provides a temporary HTTP server to handle OAuth callbacks
during the authentication flow, similar to Home Assistant's implementation.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from aiohttp import web
from urllib.parse import urlparse, parse_qs

_LOG = logging.getLogger("OAUTH_SERVER")

class OAuthCallbackServer:
    """Temporary HTTP server to handle OAuth callbacks."""

    def __init__(self, port: int = 8080):
        self.port = port
        self.app = web.Application()
        self.runner = None
        self.site = None
        self.auth_code = None
        self.code_received = asyncio.Event()

        # Setup routes
        self.app.router.add_get('/callback', self.handle_callback)
        self.app.router.add_get('/', self.handle_root)

    async def handle_callback(self, request):
        """Handle OAuth callback with authorization code."""
        try:
            # Extract code from query parameters
            code = request.query.get('code')
            error = request.query.get('error')

            if error:
                _LOG.error(f"OAuth error: {error}")
                error_description = request.query.get('error_description', 'Unknown error')
                html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Xbox Authentication - Error</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #f5f5f5; }}
                        .container {{ background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto; }}
                        h1 {{ color: #e74c3c; }}
                        .error {{ color: #e74c3c; padding: 20px; background: #fee; border-radius: 5px; margin: 20px 0; }}
                        .close-msg {{ color: #666; margin-top: 20px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Authentication Failed</h1>
                        <div class="error">
                            <strong>Error:</strong> {error}<br>
                            <strong>Description:</strong> {error_description}
                        </div>
                        <p class="close-msg">You can close this window and try again.</p>
                    </div>
                </body>
                </html>
                """
                return web.Response(text=html, content_type='text/html')

            if not code:
                _LOG.error("No authorization code received")
                html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Xbox Authentication - Error</title>
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #f5f5f5; }
                        .container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto; }
                        h1 { color: #e74c3c; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Authentication Failed</h1>
                        <p>No authorization code was received.</p>
                        <p>You can close this window and try again.</p>
                    </div>
                </body>
                </html>
                """
                return web.Response(text=html, content_type='text/html')

            # Store the code and signal that we received it
            self.auth_code = code
            self.code_received.set()
            _LOG.info(f"Successfully received authorization code (length: {len(code)})")

            # Return success page
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Xbox Authentication - Success</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #f5f5f5; }
                    .container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto; }
                    h1 { color: #107c10; }
                    .checkmark { font-size: 60px; color: #107c10; margin: 20px 0; }
                    .success-msg { color: #107c10; padding: 20px; background: #f0f8f0; border-radius: 5px; margin: 20px 0; }
                    .close-msg { color: #666; margin-top: 20px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="checkmark">&#10004;</div>
                    <h1>Authentication Successful!</h1>
                    <div class="success-msg">
                        <strong>You have successfully authenticated with Xbox Live.</strong>
                    </div>
                    <p>The integration will now complete the setup automatically.</p>
                    <p class="close-msg">You can close this window now.</p>
                </div>
                <script>
                    // Auto-close after 3 seconds
                    setTimeout(function() {
                        window.close();
                    }, 3000);
                </script>
            </body>
            </html>
            """
            return web.Response(text=html, content_type='text/html')

        except Exception as e:
            _LOG.exception(f"Error handling OAuth callback: {e}")
            return web.Response(text="Internal server error", status=500)

    async def handle_root(self, request):
        """Handle root path."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Xbox Authentication Server</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #f5f5f5; }
                .container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Xbox Authentication Server</h1>
                <p>This server is running to handle OAuth authentication.</p>
                <p>Please complete the authentication in your browser.</p>
            </div>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')

    async def start(self):
        """Start the OAuth callback server."""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, 'localhost', self.port)
            await self.site.start()
            _LOG.info(f"OAuth callback server started on http://localhost:{self.port}")
        except Exception as e:
            _LOG.exception(f"Failed to start OAuth callback server: {e}")
            raise

    async def stop(self):
        """Stop the OAuth callback server."""
        try:
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
            _LOG.info("OAuth callback server stopped")
        except Exception as e:
            _LOG.exception(f"Error stopping OAuth callback server: {e}")

    async def wait_for_code(self, timeout: int = 300):
        """
        Wait for authorization code with timeout.

        Args:
            timeout: Maximum time to wait in seconds (default 5 minutes)

        Returns:
            Authorization code if received, None if timeout
        """
        try:
            await asyncio.wait_for(self.code_received.wait(), timeout=timeout)
            return self.auth_code
        except asyncio.TimeoutError:
            _LOG.error(f"Timeout waiting for authorization code after {timeout} seconds")
            return None
