# Iconomi Integration for Home Assistant

## Installation

### Iconomi
Create an API key in your Iconomi account. Go to https://www.iconomi.com/settings/api-keys and click "Create API Key". Give it a fancy name and click "Create".

### Home Assistant
```yaml
# Example configuration.yaml entry
sensor:
  - platform: iconomi
    api_key: !secret iconomi_api_key
    api_secret: !secret iconomi_api_secret  
```

## Donkey Bridges

```bash
git commit -a --no-verify
```