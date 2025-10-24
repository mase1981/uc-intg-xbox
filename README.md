# Xbox Integration for Unfolded Circle Remote

![xbox](https://img.shields.io/badge/xbox-gaming-green)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-xbox)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-xbox/total)
![License](https://img.shields.io/badge/license-MPL--2.0-blue)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA)](https://github.com/sponsors/mase1981/button)


> **Control your Xbox One, Xbox Series S, or Xbox Series X console with the Unfolded Circle Remote 2/3**

Full remote control integration for Xbox consoles providing dashboard navigation, power management, and media playback directly from your Unfolded Circle Remote Two and Remote 3.

---

## 🎮 Supported Consoles

This integration works with:

- 🎮 **Xbox One** (Original, S, X)
- 🎮 **Xbox Series S**
- 🎮 **Xbox Series X**

---

## ✨ Features

### Remote Control
- ✅ **Power Control** - Turn console on/off (requires Instant-On/Sleep mode)
- ✅ **Dashboard Navigation** - Full D-Pad control with system buttons
- ✅ **Menu Controls** - Home, Menu, View, Back navigation
- ✅ **Button Mapping** - A, B, X, Y buttons for selections
- ✅ **Media Playback** - Play, Pause, Stop, skip tracks
- ✅ **Volume Control** - Control TV volume via HDMI-CEC
- ✅ **OAuth2 Authentication** - Secure Microsoft account login
- ✅ **Automatic Discovery** - Integration discoverable on network

---

## 📋 Requirements

- **Unfolded Circle Remote Two** or **Remote 3** (firmware 1.6.0+)
- **Xbox Console** (One, Series S, or Series X)
- **Microsoft Account** with Xbox Live access
- **Xbox Live Device ID** (found in console settings)
- **Network Connectivity** between Remote and Xbox
- **Console Power Mode**: Set to **Sleep** (formerly "Instant-On") for power on functionality

### Console Configuration Required

1. Enable **Remote Features** on your Xbox:
   - Go to `Settings > Devices & connections > Remote features`
   - Check "Enable remote features"
2. Set Power Mode to **Sleep**:
   - Go to `Settings > General > Power options`
   - Select "Sleep" power mode
3. Find your **Xbox Live Device ID**:
   - Located at `Settings > Devices & connections > Remote features`
   - Copy the long alphanumeric ID

---

## 🚀 Installation

### Method 1: Remote Web Configurator (Recommended)

1. Download the latest `uc-intg-xbox-X.X.X.tar.gz` from [Releases](https://github.com/mase1981/uc-intg-xbox/releases)
2. Open your Unfolded Circle **Web Configurator** (http://remote-ip/)
3. Navigate to **Integrations** → **Add Integration**
4. Click **Upload Driver**
5. Select the downloaded `.tar.gz` file
6. Follow the on-screen setup wizard

### Method 2: Docker Run (One-Line Command)
```bash
docker run -d --name uc-intg-xbox --restart unless-stopped --network host -v $(pwd)/data:/data -e UC_CONFIG_HOME=/data -e UC_INTEGRATION_INTERFACE=0.0.0.0 -e UC_INTEGRATION_HTTP_PORT=9094 -e UC_DISABLE_MDNS_PUBLISH=false ghcr.io/mase1981/uc-intg-xbox:latest
```

### Method 3: Docker Compose

Create a `docker-compose.yml` file:
```yaml
version: '3.8'

services:
  xbox-integration:
    image: ghcr.io/mase1981/uc-intg-xbox:latest
    container_name: uc-intg-xbox
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./data:/data
    environment:
      - UC_CONFIG_HOME=/data
      - UC_INTEGRATION_INTERFACE=0.0.0.0
      - UC_INTEGRATION_HTTP_PORT=9094
      - UC_DISABLE_MDNS_PUBLISH=false
```

Then run:
```bash
docker-compose up -d
```

> **Note**: If mDNS discovery doesn't work with Docker, click **Advanced** when adding the integration and manually enter the container IP: `ws://CONTAINER_IP:9094/`

### Method 4: Python (Development)
```bash
# Clone repository
git clone https://github.com/mase1981/uc-intg-xbox.git
cd uc-intg-xbox

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run integration
python -m uc_intg_xbox.driver
```

---

## ⚙️ Configuration

### Step 1: Obtain Your Xbox Live Device ID

1. On your Xbox console, navigate to:
   - `Settings > Devices & connections > Remote features`
2. Find **Xbox Live Device ID** (a long alphanumeric string)
3. Write it down or take a photo - you'll need it for setup

### Step 2: Setup in Remote Configurator

1. In the UC Remote web configurator, go to **Integrations**
2. Find **Xbox Integration** and click **Configure**
3. Enter your **Xbox Live Device ID** from Step 1
4. Click **Next**
5. A **Login URL** will be displayed - copy it completely
6. Open the URL in a web browser and log in with your Microsoft account
7. After successful login, you'll be redirected to a blank page
8. **Copy the entire URL** from your browser's address bar
9. Paste the URL back into the integration setup field
10. Complete the setup

### Step 3: Add Remote Entity (If Needed)

If the Xbox Remote entity doesn't appear automatically:
1. Go to the **Xbox Integration** settings page
2. Find **Configured Entities**
3. Tap **Add** next to "Xbox Remote"
4. The entity will now be available for use

---

## 🎮 Usage

### Entity Created

**Xbox Remote Entity**
- **Entity ID**: `xbox-{device_id}`
- **Name**: `Xbox ({device_id})`
- **Type**: Remote

**Features:**
- Power on/off
- Full D-Pad navigation (Up, Down, Left, Right)
- System buttons (Home, Menu, View, Back)
- Action buttons (A, B, X, Y)
- Media playback (Play, Pause, Stop, Next, Previous)
- Volume control via HDMI-CEC
- Color buttons (Red/B, Green/A, Blue/X, Yellow/Y)

### Adding to Activities

1. Create or edit an **Activity**
2. Add the **Xbox Remote** entity
3. Map power on/off commands
4. Configure button shortcuts as needed
5. Save the activity

### Dashboard Navigation

The integration provides complete Xbox dashboard navigation:
- **D-Pad**: Navigate menus and UI
- **A Button**: Select/Confirm
- **B Button**: Back/Cancel
- **Home**: Return to dashboard
- **Menu**: Context menu
- **View**: Options/View button

---

## 🎛️ Button Mapping

Complete mapping of Xbox remote commands:

| Remote Command | Xbox Function | Description |
|---------------|---------------|-------------|
| **ON** | Power On | Turn console on (requires Sleep mode) |
| **OFF** | Power Off | Turn console off |
| **↑ UP** | D-Pad Up | Navigate up in menus |
| **↓ DOWN** | D-Pad Down | Navigate down in menus |
| **← LEFT** | D-Pad Left | Navigate left in menus |
| **→ RIGHT** | D-Pad Right | Navigate right in menus |
| **SELECT** | A Button | Confirm/Select |
| **BACK** | B Button | Back/Cancel |
| **HOME** | Xbox Button | Return to dashboard |
| **MENU** | Menu Button | Open context menu |
| **VIEW** | View Button | Options/View |
| **A_BUTTON** | A Button | Green button / Select |
| **B_BUTTON** | B Button | Red button / Back |
| **X_BUTTON** | X Button | Blue button |
| **Y_BUTTON** | Y Button | Yellow button |
| **PLAY** | Play | Resume playback |
| **PAUSE** | Pause | Pause playback |
| **STOP** | Stop | Stop playback |
| **NEXT_TRACK** | Next | Next track/chapter |
| **PREVIOUS_TRACK** | Previous | Previous track/chapter |
| **VOLUME_UP** | Volume Up | Increase TV volume (via CEC) |
| **VOLUME_DOWN** | Volume Down | Decrease TV volume (via CEC) |
| **MUTE_TOGGLE** | Mute | Mute/unmute TV (via CEC) |
| **RED** | B Button | Red function key |
| **GREEN** | A Button | Green function key |
| **BLUE** | X Button | Blue function key |
| **YELLOW** | Y Button | Yellow function key |

---

## 🔧 Troubleshooting

### Power On Not Working

**Problem**: Cannot turn on Xbox console

**Solutions:**
1. ✅ Verify console is in **Sleep** power mode (not Energy Saving)
   - Go to `Settings > General > Power options`
   - Select "Sleep" mode
2. ✅ Ensure Remote Features are enabled on Xbox
3. ✅ Console must be on the same network as the Remote
4. ✅ Give the console 30-60 seconds after entering sleep to become fully available

### Authentication Failed

**Problem**: Setup fails during OAuth login

**Solutions:**
1. ✅ Ensure you're using the correct Microsoft account (the one linked to your Xbox)
2. ✅ Copy the **entire** redirect URL including all parameters
3. ✅ Don't modify the URL - paste it exactly as shown in browser
4. ✅ Try logging out of Microsoft account and logging in again
5. ✅ Check that you have proper Xbox Live access on your account

### Commands Not Responding

**Problem**: Buttons don't control the console

**Solutions:**
1. ✅ Verify Xbox is powered on
2. ✅ Check that console is on the network (test with Xbox app)
3. ✅ Restart the integration from web configurator
4. ✅ Check integration logs for authentication errors
5. ✅ Re-authenticate if tokens have expired (typically every 90 days)

### Volume Control Not Working

**Problem**: Volume up/down/mute buttons have no effect

**Explanation**: 
Xbox controls TV volume via **HDMI-CEC** only. The commands are sent to your TV through the HDMI cable, not directly to the Xbox.

**Solutions:**
1. ✅ Enable HDMI-CEC on your TV:
   - Samsung: "Anynet+"
   - LG: "Simplink"
   - Sony: "Bravia Sync"
   - Panasonic: "VIERA Link"
   - Philips: "EasyLink"
2. ✅ Verify HDMI cable connects Xbox to TV
3. ✅ Check TV settings for CEC/external device control
4. ✅ Some TVs require enabling CEC per HDMI input

### Entities Unavailable After Reboot

**Problem**: After restarting UC Remote, entity shows as "unavailable"

**Solutions:**
1. ✅ Integration includes reboot survival - wait 30-60 seconds for reconnection
2. ✅ Tokens are refreshed automatically on startup
3. ✅ Check that Xbox is powered on and connected
4. ✅ Review integration logs for connection errors

### mDNS Discovery Not Working

**Problem**: Integration doesn't appear in available integrations

**Solutions:**
1. ✅ If using Docker, click **Advanced** when adding integration
2. ✅ Enter container IP manually: `ws://CONTAINER_IP:9094/`
3. ✅ Verify network_mode is set to `host` in docker-compose
4. ✅ Check firewall settings aren't blocking port 9094

---

## ⚠️ Known Limitations

| Limitation | Explanation | Workaround |
|-----------|-------------|------------|
| **No Media App Control** | Integration cannot control third-party media apps (Netflix, YouTube, etc.) | This is a limitation of the public Xbox Web API for security/DRM reasons |
| **Dashboard Only** | Full control works on Xbox dashboard but limited in apps | Use physical controller for app-specific functions |
| **Sleep Mode Required** | Power On only works in Sleep mode, not Energy Saving | Change power mode in Xbox settings |
| **Volume via CEC Only** | Volume commands use HDMI-CEC to control TV | Enable CEC on your TV settings |
| **Internet Dependency** | Commands are sent via Xbox Live API (cloud) | Some responses may have delays if internet is slow |
| **Token Expiration** | OAuth tokens expire periodically (~90 days) | Re-authenticate when tokens expire |

---

## 🏗️ Architecture

### Integration Components
```
uc-intg-xbox/
├── uc_intg_xbox/
│   ├── __init__.py           # Package initialization with version
│   ├── auth.py               # Xbox OAuth2 authentication handler
│   ├── config.py             # Configuration management with persistence
│   ├── driver.py             # Main integration driver with token refresh
│   ├── media_player.py       # Remote Control entity implementation
│   ├── setup.py              # Setup flow handler (renamed from setup_manager)
│   └── xbox_device.py        # Xbox Web API client wrapper
├── driver.json               # Integration metadata
├── pyproject.toml            # Python project configuration
├── requirements.txt          # Runtime dependencies
├── Dockerfile                # Docker image definition
├── docker-compose.yml        # Docker Compose configuration
├── LICENSE                   # MPL-2.0 license
└── README.md                # This file
```

### Dependencies

- **ucapi** (>=0.3.1) - Unfolded Circle Integration API
- **xbox-webapi-python** - Xbox Live Web API client
- **pydantic** (>=2.0) - Data validation
- **httpx** - Async HTTP client
- **certifi** - SSL certificate verification
- **requests** - HTTP library

---

## 👨‍💻 Development

### Building From Source
```bash
# Clone repository
git clone https://github.com/mase1981/uc-intg-xbox.git
cd uc-intg-xbox

# Install in development mode
pip install -e ".[dev]"

# Run tests (when available)
pytest

# Build distribution package
python -m build

# Output: dist/uc-intg-xbox-X.X.X.tar.gz
```

### Contributing

Contributions are welcome! Please follow these guidelines:

1. 🍴 Fork the repository
2. 🌿 Create a feature branch (`git checkout -b feature/amazing-feature`)
3. 💾 Commit your changes (`git commit -m 'Add amazing feature'`)
4. 📤 Push to the branch (`git push origin feature/amazing-feature`)
5. 🎉 Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints where applicable
- Add docstrings to all functions and classes
- Keep line length to 100 characters
- Use absolute imports for clarity

---

## 🙏 Credits & Acknowledgments

### Integration Development
- **Author**: [Meir Miyara](https://github.com/mase1981)

### Libraries & References
- **xbox-webapi-python**: [OpenXbox/xbox-webapi-python](https://github.com/OpenXbox/xbox-webapi-python) - Python library for Xbox Live API
- **Unfolded Circle**: [Integration Python Library](https://github.com/unfoldedcircle/integration-python-library)

### Special Thanks
- **Jack Powell** ([@JackJPowell](https://github.com/JackJPowell)) - PSN and JVC integrations as reference
- **Mike Hobin** ([@mikehobin](https://github.com/mikehobin)) - Docker configuration assistance
- **Unfolded Circle Community** - Testing and feedback

---

## 💖 Support the Project

If you find this integration useful, please consider:

- ⭐ **Star this repository** on GitHub
- 🐛 **Report issues** to help improve the integration
- 💡 **Share feedback** in discussions
- 📖 **Contribute** documentation or code improvements

### Sponsor

If you'd like to support continued development:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-yellow?logo=buy-me-a-coffee)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-Donate-blue?logo=paypal)](https://paypal.me/mmiyara)

---

## 📞 Support & Community

### Getting Help

- 📋 **Issues**: [GitHub Issues](https://github.com/mase1981/uc-intg-xbox/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/mase1981/uc-intg-xbox/discussions)
- 🎮 **Discord**: [Unfolded Circle Community](https://discord.gg/zGVYf58)
- 🌐 **UC Community**: [Unfolded Circle Forum](https://unfoldedcircle.com/community)

### Reporting Issues

When reporting issues, please include:

1. Integration version
2. Xbox console model
3. UC Remote firmware version
4. Detailed description of the problem
5. Steps to reproduce
6. Relevant log excerpts

---

## 📜 License

This project is licensed under the **Mozilla Public License 2.0** (MPL-2.0).

See the [LICENSE](LICENSE) file for full details.
```
Copyright (c) 2025 Meir Miyara

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
```

---

<div align="center">

**Enjoy controlling your Xbox console with your Unfolded Circle Remote!** 🎉

Made with ❤️ by [Meir Miyara](https://github.com/mase1981)

</div>