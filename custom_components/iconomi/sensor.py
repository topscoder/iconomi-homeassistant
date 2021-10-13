"""Iconomi sensor platform."""
import asyncio
import json
import logging
import base64
import hashlib
import hmac
import re
import time
import voluptuous as vol
import aiohttp
from datetime import timedelta

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.discovery import async_load_platform
from .const import (
    DOMAIN,
    API_URL,
    CONF_ATTRIBUTION,
    CONF_NAME,
    CONF_API_KEY,
    CONF_API_SECRET,
    DEFAULT_SCAN_INTERVAL,
)

REQUIREMENTS = []

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Iconomi Performance"
DEFAULT_ICON = "mdi:currency-btc"

SCAN_INTERVAL = timedelta(minutes=DEFAULT_SCAN_INTERVAL)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME, default="iconomi"): cv.string,
        vol.Required(CONF_API_KEY, default="Required api_key is missing."): cv.string,
        vol.Required(
            CONF_API_SECRET, default="Required api_secret is missing."
        ): cv.string,
        vol.Required("datatype", default="user_balance"): cv.string,
    }
)

class IconomiConfig(object):
    name: str
    api_key: str
    api_secret: str
    datatype: str

    def __init__(self, config) -> None:
        self.name = config.get(CONF_NAME)
        self.api_key = config.get(CONF_API_KEY)
        self.api_secret = config.get(CONF_API_SECRET)
        self.datatype = config.get("datatype")

@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    iconomi_config = IconomiConfig(config)
    async_add_devices([IconomiSensor(hass, iconomi_config)], update_before_add=True)

async def async_get_pdata(self, endpoint):
    json_resp = {}
    jsonPayload = ""
    method = "GET"
    timestamp = str(int(time.time() * 1000.0))

    requestHeaders = {
        "ICN-API-KEY": self._config.api_key,
        "ICN-SIGN": self.generate_signature(jsonPayload, method, endpoint, timestamp),
        "ICN-TIMESTAMP": timestamp,
    }

    url = f"{API_URL}{endpoint}"

    async with self._session.get(
        url, headers=requestHeaders, verify_ssl=False
    ) as response:
        rsp1 = await response.text()
        json_resp = json.loads(rsp1)

    return json_resp


class IconomiSensor(Entity):
    def __init__(self, hass, iconomi_config: IconomiConfig):
        """Initialize the sensor."""
        self._hass = hass
        self._name = iconomi_config.name
        self._config = iconomi_config
        self._state = None
        self._pdata = []
        self._icon = DEFAULT_ICON
        self._attr = {}
        self._attr["provider"] = CONF_ATTRIBUTION
        self._session = async_get_clientsession(hass)

    @property
    def device_state_attributes(self):
        return self._attr

    @asyncio.coroutine
    async def async_update(self):

        endpoint = "/v1/user/balance"

        try:
            pdata = await async_get_pdata(self, endpoint)
        except Exception as ex:
            pdata = "No data returned from API"
            _LOGGER.error(ex)

        self._pdata = pdata
        self._attr["raw"] = pdata

        # Calc sum of balances and set as state value
        value_usd = 0
        for item in pdata["daaList"]:
            value_usd = value_usd + float(item["value"])

        # Also add crypto values
        for asset in pdata["assetList"]:
            value_usd = value_usd + float(asset["value"])

        self._state = round(value_usd, 2)
        return self._state

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return DEFAULT_ICON

    def generate_signature(self, payload, request_type, request_path, timestamp):
        """Generate signature for private (user specific) API calls"""
        data = "".join([timestamp, request_type.upper(), request_path, payload])
        signed_data = hmac.new(
            self._config.api_secret.encode(), data.encode(), hashlib.sha512
        )
        base64_encoded_data = base64.b64encode(signed_data.digest())
        return base64_encoded_data.decode("utf-8")
