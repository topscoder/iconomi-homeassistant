"""Iconomi sensor platform."""
import base64
from datetime import timedelta
import hashlib
import hmac
import json
import logging
import time
from typing import Any, Callable, Dict, Optional
import unittest

from aiohttp import ClientError
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ATTR_NAME, CONF_ACCESS_TOKEN
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
import requests
import voluptuous as vol

from .const import API_URL, BASE_API_URL, CONF_API_KEY, CONF_API_SECRET

# API_URL = "https://api.iconomi.com"
# API_SECRET = "<YOUR_SECRET>"
# API_KEY = "<YOUR_KEY>"

_LOGGER = logging.getLogger(__name__)
# Time between updating data from GitHub
SCAN_INTERVAL = timedelta(minutes=10)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ACCESS_TOKEN): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_API_SECRET): cv.string,
        # vol.Required(CONF_API_URL): cv.url,
    }
)

async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    """Set up the sensor platform."""
    #session = async_get_clientsession(hass)
    # github = GitHubAPI(session, "requester", oauth_token=config[CONF_ACCESS_TOKEN])
    # sensors = [GitHubRepoSensor(github, repo) for repo in config[CONF_REPOS]]
    sensors = [IconomiSensor(config[CONF_API_KEY], config[CONF_API_SECRET])]
    async_add_entities(sensors, update_before_add=True)


class IconomiSensor(Entity):
    """Representation of an Iconomi API sensor."""

    def __init__(self, api_key: str, api_secret: str):
        super().__init__()

        self._name = "Iconomi API"
        self._api_key = api_key
        self._api_secret = api_secret
        self._state = None
        self._available = True

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    # @property
    # def unique_id(self) -> str:
    #     """Return the unique ID of the sensor."""
    #     return self.repo

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def state(self) -> Optional[str]:
        return self._state

    @property
    def device_state_attributes(self) -> Dict[str, Any]:
        return self.attrs

    async def async_update(self):
        try:            
            self.attrs["strategies"] = await self.get('/v1/strategies')
            self.attrs["user_activity"] = await self.get('/v1/user/activity')
            
            # Set state to short commit sha.
            self._state = str(int(time.time() * 1000.0)) # FIXME Pick something which represents the current state (datetime, current value, )
            self._available = True
        except (ClientError):
            self._available = False
            _LOGGER.exception("Error retrieving data from Iconomi.")

    def generate_signature(self, payload, request_type, request_path, timestamp): 
        data = ''.join([timestamp, request_type.upper(), request_path, payload]).encode()
        signed_data = hmac.new(self._api_secret.encode(), data, hashlib.sha512)
        return base64.b64encode(signed_data.digest())

    def get(self, api):      
        self.call('GET', api, '')

    def post(self, api, payload):
        self.call('POST', api, payload)
        
    def call(self, method, api, payload):
        timestamp = str(int(time.time() * 1000.0))

        jsonPayload = payload
        if method == 'POST':
          jsonPayload = json.dumps(payload)

        requestHeaders = { 
            'ICN-API-KEY' : self._api_key,
            'ICN-SIGN' : self.generate_signature(jsonPayload, method, api, timestamp),
            'ICN-TIMESTAMP' : timestamp
        }

        if method == 'GET': 
          response = requests.get(API_URL + api, headers = requestHeaders)
          if response.status_code == 200:
            _LOGGER.exception(json.dumps(json.loads(response._content), indent=4, sort_keys=True))
          else:
            _LOGGER.exception('Request did not succeed: ' + response.reason)
        elif method == 'POST':
          response = requests.post(API_URL + api, json = payload, headers = requestHeaders)
          if response.status_code == 200:
            _LOGGER.exception(json.dumps(json.loads(response._content), indent=4, sort_keys=True))
          else:
            _LOGGER.exception('Request did not succeed: ' + response.reason)
