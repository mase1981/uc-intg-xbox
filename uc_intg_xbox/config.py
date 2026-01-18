"""
Xbox configuration module for Unfolded Circle integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime

_LOG = logging.getLogger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

@dataclass
class ConsoleConfig:
    """Configuration for a single Xbox console."""
    liveid: str
    name: str
    enabled: bool = True

@dataclass
class XboxConfig:
    client_id: str | None = None
    client_secret: str | None = None
    tokens: dict | None = field(default_factory=dict)
    consoles: list[dict] | None = field(default_factory=list)  # List of ConsoleConfig dicts

    # Legacy support for single console setups
    liveid: str | None = None

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.tokens and
                   (self.consoles or self.liveid))

    def get_consoles(self) -> list[ConsoleConfig]:
        """Get list of console configurations."""
        console_list = []

        # Handle legacy single console config
        if self.liveid and not self.consoles:
            console_list.append(ConsoleConfig(
                liveid=self.liveid,
                name="Xbox Console",
                enabled=True
            ))
        # Handle new multi-console config
        elif self.consoles:
            for console_data in self.consoles:
                console_list.append(ConsoleConfig(**console_data))

        return console_list

    def add_console(self, liveid: str, name: str, enabled: bool = True):
        """Add a console to the configuration."""
        if not self.consoles:
            self.consoles = []

        # Check if console already exists
        for console in self.consoles:
            if console.get('liveid') == liveid:
                console['name'] = name
                console['enabled'] = enabled
                return

        # Add new console
        self.consoles.append({
            'liveid': liveid,
            'name': name,
            'enabled': enabled
        })

        # Clear legacy liveid if migrating
        if self.liveid == liveid:
            self.liveid = None

    def reload_from_disk(self, config_path: str):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            self.client_id = config_data.get("client_id")
            self.client_secret = config_data.get("client_secret")
            self.tokens = config_data.get("tokens")
            self.consoles = config_data.get("consoles", [])
            # Legacy support
            self.liveid = config_data.get("liveid")
            _LOG.info("Configuration reloaded from disk.")
        except (FileNotFoundError, json.JSONDecodeError):
            _LOG.debug("No configuration file found to reload.")
        except Exception as e:
            _LOG.exception("Failed to reload configuration from disk", exc_info=e)

    async def load(self, api):
        config_path = os.path.join(api.config_dir_path, "config.json")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            self.client_id = config_data.get("client_id")
            self.client_secret = config_data.get("client_secret")
            self.tokens = config_data.get("tokens")
            self.consoles = config_data.get("consoles", [])
            # Legacy support
            self.liveid = config_data.get("liveid")
            _LOG.info("Configuration loaded successfully.")
        except (FileNotFoundError, json.JSONDecodeError):
            _LOG.info("Configuration file not found or is invalid.")
        except Exception as e:
            _LOG.exception("Failed to load configuration", exc_info=e)

    async def save(self, api):
        config_path = os.path.join(api.config_dir_path, "config.json")
        os.makedirs(api.config_dir_path, exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, indent=4, cls=DateTimeEncoder)
        _LOG.info("Configuration saved successfully.")