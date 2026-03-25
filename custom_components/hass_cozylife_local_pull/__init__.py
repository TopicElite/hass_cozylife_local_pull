"""CozyLife Local Pull integration."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.typing import ConfigType
import logging
import time
from .const import (
    DOMAIN,
    LANG
)
from .utils import get_pid_list
from .udp_discover import get_ip
from .tcp_client import tcp_client


_LOGGER = logging.getLogger(__name__)


def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """
    Set up the CozyLife integration.
    config example: {'lang': 'zh', 'ip': ['192.168.5.201', '192.168.5.202']}
    """
    ip = get_ip()
    ip_from_config = config[DOMAIN].get('ip') if config[DOMAIN].get('ip') is not None else []
    ip += ip_from_config

    # Deduplicate while preserving order
    ip_list = list(dict.fromkeys(ip))

    if not ip_list:
        _LOGGER.info('discover nothing')
        return True

    _LOGGER.info(f'try connect ip_list: {ip_list}')

    lang_from_config = config[DOMAIN].get('lang') or LANG
    get_pid_list(lang_from_config)

    hass.data[DOMAIN] = {
        'temperature': 24,
        'ip': ip_list,
        'tcp_client': [tcp_client(item) for item in ip_list],
    }

    # Wait for devices to respond with their info via TCP.
    # Not ideal (blocks setup), but required due to the synchronous TCP design.
    time.sleep(3)

    hass.loop.call_soon_threadsafe(
        hass.async_create_task,
        async_load_platform(hass, 'light', DOMAIN, {}, config)
    )
    hass.loop.call_soon_threadsafe(
        hass.async_create_task,
        async_load_platform(hass, 'switch', DOMAIN, {}, config)
    )
    return True
