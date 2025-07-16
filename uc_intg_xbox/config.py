import json
import logging
import os
from dataclasses import asdict, dataclass, field

_LOG = logging.getLogger(__name__)

@dataclass
class XboxConfig:
    liveid: str | None = None
    tokens: dict | None = field(default_factory=dict)

    async def load(self, api):
        config_path = os.path.join(api.config_dir_path, "config.json")
        _LOG.info(f"Attempting to load config from: {config_path}")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            self.liveid = config_data.get("liveid")
            self.tokens = config_data.get("tokens")
            _LOG.info("Configuration loaded successfully.")
        except FileNotFoundError:
            _LOG.info("config.json not found. A new one will be created upon saving.")
        except Exception as e:
            _LOG.error(f"Failed to load config.json: {e}")

    async def save(self, api):
        config_path = os.path.join(api.config_dir_path, "config.json")
        _LOG.info(f"Saving config to: {config_path}")
        try:
            os.makedirs(api.config_dir_path, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self), f, indent=4)
            _LOG.info("Configuration saved successfully.")
        except Exception as e:
            _LOG.error(f"Failed to save config.json: {e}")