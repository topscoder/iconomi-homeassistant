# Iconomi Integration for Home Assistant

This sensor integrates your Iconomi portfolio value into Home Assistant. As this is a sensor, HA will handle the history and graphs for you :)

## Installation

Create an API key in your Iconomi account. Go to https://www.iconomi.com/settings/api-keys and click "Create API Key". Give it a fancy name and click "Create". NOTE: Your API Secret will only be shown ONCE. So copy and store it safely in your digital vault.

Install using HACS. Add this GitHub repo as custom repository using repo URL `https://github.com/topscoder/iconomi-homeassistant`

```yaml
# Example configuration.yaml entry
sensor:
  - platform: iconomi
    name: "Iconomi Balance"
    api_key: !secret iconomi_api_key
    api_secret: !secret iconomi_api_secret

# Example secrets.yaml entry
# Get your keys from https://www.iconomi.com/settings/api-keys
iconomi_api_key: "abcd1337"
iconomi_api_secret: "ef1337ab"
```

## Donkey Bridges

```bash
git commit -a --no-verify
```