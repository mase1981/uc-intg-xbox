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
class XboxConfig:
    client_id: str | None = None
    client_secret: str | None = None
    liveid: str | None = None
    tokens: dict | None = field(default_factory=dict)

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.liveid and self.tokens)

    def reload_from_disk(self, config_path: str):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            self.client_id = config_data.get("client_id")
            self.client_secret = config_data.get("client_secret")
            self.liveid = config_data.get("liveid")
            self.tokens = config_data.get("tokens")
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
            self.liveid = config_data.get("liveid")
            self.tokens = config_data.get("tokens")
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