"""
Constants for Xbox integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

POLL_INTERVAL = 15  # console status (power, playback, app in focus)
POLL_INTERVAL_OFF = 90  # unused since 5.3.0, kept for reference
PROFILE_EVERY = 4  # polls between profile updates (1 minute)
FRIENDS_EVERY = 20  # polls between friends updates (5 minutes)
CONSOLES_EVERY = 40  # polls between console list / storage updates (10 minutes)
PRESENCE_LAG = 120  # seconds Xbox Live presence may still show the previous app
MAX_CONSECUTIVE_FAILURES = 5
RECONNECT_INTERVAL = 30  # first reconnect attempt, doubles on failure
RECONNECT_MAX = 900  # longest wait between reconnect attempts
TOKEN_REFRESH_INTERVAL = 12 * 60 * 60
OAUTH_CALLBACK_PORT = 8765
OAUTH_REDIRECT_URI = "http://localhost:8765/callback"
TITLEHUB_CONCURRENCY = 8
