"""
Xbox configuration module.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from dataclasses import dataclass, field

from ucapi_framework import BaseConfigManager


@dataclass
class XboxConfig:
    identifier: str = ""
    name: str = ""
    liveid: str = ""
    client_id: str = ""
    client_secret: str = ""
    access_token: str = ""
    refresh_token: str = ""
    token_type: str = ""
    expires_in: int = 0
    scope: str = ""
    user_id: str = ""
    issued: str = ""
    tokens: dict = field(default_factory=dict)


class XboxConfigManager(BaseConfigManager[XboxConfig]):
    pass
