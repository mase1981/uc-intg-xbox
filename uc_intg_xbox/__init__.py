"""
Xbox Integration for Unfolded Circle Remote Two/3.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path


def _get_driver_json_path() -> str:
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "driver.json")
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "driver.json"))


try:
    with open(_get_driver_json_path(), "r", encoding="utf-8") as f:
        __version__ = json.load(f).get("version", "0.0.0")
except (FileNotFoundError, json.JSONDecodeError):
    __version__ = "0.0.0"


async def main():
    from ucapi import DeviceStates
    from ucapi_framework import BaseConfigManager, get_config_path

    from uc_intg_xbox.config import XboxConfig
    from uc_intg_xbox.driver import XboxDriver
    from uc_intg_xbox.setup_flow import XboxSetupFlow

    level = os.getenv("UC_LOG_LEVEL", "DEBUG").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.DEBUG),
        format="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
    )
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("websockets.server").setLevel(logging.CRITICAL)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    _LOG = logging.getLogger(__name__)
    _LOG.info("Starting Xbox Integration v%s", __version__)

    driver = XboxDriver()
    config_path = get_config_path(driver.api.config_dir_path or "")
    config_manager = BaseConfigManager(
        config_path,
        add_handler=driver.on_device_added,
        remove_handler=driver.on_device_removed,
        config_class=XboxConfig,
    )
    driver.config_manager = config_manager

    setup_handler = XboxSetupFlow.create_handler(driver)
    await driver.api.init(_get_driver_json_path(), setup_handler)
    await driver.register_all_device_instances(connect=False)

    device_count = len(list(config_manager.all()))
    await driver.api.set_device_state(
        DeviceStates.CONNECTED if device_count > 0 else DeviceStates.DISCONNECTED
    )
    _LOG.info("Xbox Integration started - %d device(s) configured", device_count)
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
