#!/usr/bin/env python3
"""
Integration driver library for Remote Two.

:copyright: (c) 2023 by Unfolded Circle ApS.
:license: MPL-2.0, see LICENSE for more details.
"""

# Set default logging handler to avoid "No handler found" warnings.
import logging  # isort:skip

from .api_definitions import (  # isort:skip # noqa: F401
    AbortDriverSetup,
    DeviceStates,
    DriverSetupRequest,
    Events,
    IntegrationSetupError,
    RequestUserConfirmation,
    RequestUserInput,
    SetupAction,
    SetupComplete,
    SetupDriver,
    SetupError,
    StatusCodes,
    UserConfirmationResponse,
    UserDataResponse,
)
from .entity import Entity, EntityTypes  # isort:skip # noqa: F401
from .entities import Entities  # isort:skip # noqa: F401
from .api import IntegrationAPI  # isort:skip # noqa: F401

# Entity types
from .button import Button  # noqa: F401
from .climate import Climate  # noqa: F401
from .cover import Cover  # noqa: F401
from .light import Light  # noqa: F401
from .media_player import MediaPlayer  # noqa: F401
from .remote import Remote  # noqa: F401
from .sensor import Sensor  # noqa: F401
from .switch import Switch  # noqa: F401

try:
    from ._version import version as __version__
    from ._version import version_tuple
except ImportError:
    __version__ = "unknown version"
    version_tuple = (0, 0, "unknown version")

logging.getLogger(__name__).addHandler(logging.NullHandler())
