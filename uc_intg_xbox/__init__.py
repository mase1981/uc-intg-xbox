#!/usr/bin/env python3
"""
Xbox Integration for Unfolded Circle Remote Two/3.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import json
import logging
from pathlib import Path

logging.getLogger(__name__).addHandler(logging.NullHandler())

# Load version from driver.json (same pattern as other integrations)
try:
    driver_path = Path(__file__).parent.parent / "driver.json"
    with open(driver_path, "r", encoding="utf-8") as f:
        driver_info = json.load(f)
        __version__ = driver_info.get("version", "0.0.0")
except (FileNotFoundError, json.JSONDecodeError, KeyError):
    __version__ = "0.0.0"

__all__ = ["__version__"]