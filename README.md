# Xbox Integration for Unfolded Circle Remote 2/3

Control your Xbox One, Xbox Series S, or Xbox Series X console with the Unfolded Circle Remote 2 or Remote 3 with comprehensive dashboard navigation, power management, **currently playing game display**, and media playback directly from your remote.

![Xbox](https://img.shields.io/badge/xbox-gaming-green)
[![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-xbox?style=flat-square)](https://github.com/mase1981/uc-intg-xbox/releases)
![License](https://img.shields.io/badge/license-MPL--2.0-blue?style=flat-square)
[![GitHub issues](https://img.shields.io/github/issues/mase1981/uc-intg-xbox?style=flat-square)](https://github.com/mase1981/uc-intg-xbox/issues)
[![Community Forum](https://img.shields.io/badge/community-forum-blue?style=flat-square)](https://community.unfoldedcircle.com/)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-xbox/total?style=flat-square)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg?style=flat-square)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA&style=flat-square)](https://github.com/sponsors/mase1981)


## Features

This integration provides comprehensive control of your Xbox console through the Xbox Live Web API, including full remote control functionality, live gaming status display with game artwork, and seamless integration with your Unfolded Circle Remote.

---
## 💰 Support Development

If you find this integration useful, consider supporting development:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?style=for-the-badge&logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mmiyara)

Your support helps maintain this integration. Thank you! ❤️
---

### 🎮 **Remote Control**

#### **Dashboard Navigation**
- **D-Pad Control** - Full Up/Down/Left/Right navigation
- **A Button (OK)** - Select/Confirm (mapped to remote OK button)
- **B Button** - Back/Cancel
- **Home Button** - Return to Xbox dashboard
- **Menu Button** - Open context menu
- **View Button** - Options/View button

#### **Button Controls**
- **X Button** - Blue action button
- **Y Button** - Yellow action button
- **Channel Up/Down** - Y/X button shortcuts
- **Color Buttons** - Red (B), Green (A), Blue (X), Yellow (Y)

#### **Media Playback**
- **Play** - Resume playback
- **Pause** - Pause playback
- **Stop** - Stop playback
- **Next Track** - Skip forward
- **Previous Track** - Skip backward

#### **Volume Control** (via HDMI-CEC)
- **Volume Up/Down** - Adjust TV volume through Xbox
- **Mute Toggle** - Mute/unmute TV audio
- **HDMI-CEC Required** - Volume commands sent to TV via HDMI

### 📺 **Live Gaming Status Display**

#### **Media Player Entity**
Real-time display of Xbox gaming activity:
- **Currently Playing** - Shows active game title when playing
- **Game Artwork** - Displays official game cover art from Xbox Live
- **Online Status** - Shows "Online" when on dashboard
- **Offline Status** - Shows "Offline" when console is off
- **Player State** - Distinguishes between OFF, ON (dashboard), and PLAYING (in-game)

#### **Dynamic Metadata**
- **Game Title** - Current game being played
- **Xbox Gamertag** - Your Xbox Live gamertag display
- **Presence State** - Real-time activity status
- **Media Type** - Tagged as "GAME" for proper display

### 🔌 **Power Management**

#### **Power Control**
- **Power On** - Wake console from Sleep mode (requires Sleep power mode)
- **Power Off** - Turn console off
- **Power Toggle** - Toggle power state
- **Remote Startup** - Start console remotely when in Sleep mode

#### **Sleep Mode Requirement**
- **Sleep Mode Required** - Console must be in Sleep mode for remote power on
- **Energy Saving Mode** - Power on will not work in Energy Saving mode
- **Remote Features** - Must be enabled in Xbox settings

### 🌐 **Xbox Live Integration**

#### **OAuth2 Authentication**
- **Secure Login** - Microsoft account authentication via OAuth2
- **Token Management** - Automatic token refresh (12-hour intervals)
- **Session Persistence** - Maintains connection across reboots
- **Privacy Focused** - Credentials stored securely, never exposed

#### **Xbox Live API**
- **Cloud-Based Control** - Commands sent via Xbox Live servers
- **Presence Detection** - Real-time game tracking via Xbox Live
- **Title Information** - Game metadata fetched from Xbox catalog
- **Cross-Platform** - Works with Xbox One, Series S, and Series X

### 🎯 **Supported Consoles**

- **Xbox One** (Original, S, X)
- **Xbox Series S**
- **Xbox Series X**

### **Xbox Requirements**

- **Microsoft Account** - With Xbox Live access
- **Xbox Live Device ID** - Found in console settings
- **Remote Features** - Must be enabled on console
- **Sleep Power Mode** - Required for remote power on functionality
- **Network Connectivity** - Console must be connected to internet

### **Console Configuration Required**

#### Enable Remote Features:
1. Navigate to **Settings** → **Devices & connections** → **Remote features**
2. Check **"Enable remote features"**
3. Note your **Xbox Live Device ID** (long alphanumeric string)

#### Configure Sleep Mode:
1. Navigate to **Settings** → **General** → **Power options**
2. Select **"Sleep"** power mode (not Energy Saving)
3. This allows remote power on functionality

### **Network Requirements**

- **Internet Access** - Required for Xbox Live API communication
- **HTTPS** - Integration uses secure HTTPS to Xbox Live servers
- **Firewall** - Ensure outbound HTTPS traffic is permitted
- **Local Network** - Remote and Xbox should be on same network for best performance

## Installation

### Option 1: Remote Web Interface (Recommended)
1. Navigate to the [**Releases**](https://github.com/mase1981/uc-intg-xbox/releases) page
2. Download the latest `uc-intg-xbox-<version>.tar.gz` file
3. Open your remote's web interface (`http://your-remote-ip`)
4. Go to **Settings** → **Integrations** → **Add Integration**
5. Click **Upload** and select the downloaded `.tar.gz` file

### Option 2: Docker (Advanced Users)

The integration is available as a pre-built Docker image from GitHub Container Registry:

**Image**: `ghcr.io/mase1981/uc-intg-xbox:latest`

**Docker Compose:**
```yaml
services:
  uc-intg-xbox:
    image: ghcr.io/mase1981/uc-intg-xbox:latest
    container_name: uc-intg-xbox
    network_mode: host
    volumes:
      - </local/path>:/data
    environment:
      - UC_CONFIG_HOME=/data
      - UC_INTEGRATION_HTTP_PORT=9094
    restart: unless-stopped
```

**Docker Run:**
```bash
docker run -d --name=uc-intg-xbox --network host -v </local/path>:/data -e UC_CONFIG_HOME=/data -e UC_INTEGRATION_HTTP_PORT=9094 --restart unless-stopped ghcr.io/mase1981/uc-intg-xbox:latest
```

## Configuration

### Step 1: Create Azure App Registration

**IMPORTANT**: Starting with version 4.0.0, due to Microsoft OAuth changes, you must create your own Azure App Registration.

📖 **[Complete Azure Setup Guide](AZURE_SETUP_GUIDE.md)** ← Click for detailed instructions

**Quick Setup:**
1. Go to https://portal.azure.com
2. Navigate to **Microsoft Entra ID** → **App registrations**
3. Click **"+ New registration"**
4. Fill in:
   - **Name**: `Unfolded Circle Xbox Integration`
   - **Supported accounts**: Select **"Personal Microsoft accounts (e.g. Skype, Xbox)"**
   - **Redirect URI**:
     - Type: **Web**
     - URL: `http://localhost:8765/callback`
5. Click **"Register"**
6. Copy your **Application (client) ID**
7. Go to **Certificates & secrets** → Create new **Client Secret**
8. Copy the **Secret Value** (shown only once!)
9. Save both ID and Secret for integration setup

### Step 2: Prepare Your Xbox Console

**IMPORTANT**: Xbox console must be configured before adding the integration.

#### Enable Remote Features:
1. On Xbox console: **Settings** → **Devices & connections** → **Remote features**
2. Enable **"Enable remote features"**
3. Copy your **Xbox Live Device ID** (optional - v4.1.0+ can auto-discover consoles)

#### Configure Power Mode:
1. On Xbox console: **Settings** → **General** → **Power options**
2. Select **"Sleep"** power mode
3. Ensure console is connected to network

### Step 3: Setup Integration

1. After installation, go to **Settings** → **Integrations** on your Remote
2. The Xbox integration should appear in **Available Integrations**
3. Click **"Configure"** and follow the setup wizard:

#### Page 1: Enter Credentials
   - **Azure App Client ID**: Paste your Application (client) ID from Azure
   - **Azure App Client Secret**: Paste your Client Secret Value from Azure
   - **Xbox Live Device ID (Optional)**: Leave empty for automatic discovery, or paste manually
   - Click **Next**

   **🆕 v4.1.0 Auto-Discovery:** If you leave the Live ID empty, the integration will automatically discover all Xbox consoles on your Microsoft account after authentication!

#### Page 2: Microsoft Authentication

The integration uses a **hybrid authentication** system with automatic callback + manual fallback:

**🔹 Steps:**
1. **Click the Authorization URL** (opens in your browser)
2. **Sign in** with your Microsoft account (the one linked to your Xbox)
3. After signing in, Microsoft will redirect to `http://localhost:8765/callback?code=...`
4. **The page won't load** (this is normal - the server is on the Remote, not your computer)
5. **Copy the entire URL** from your browser's address bar
   - Example: `http://localhost:8765/callback?code=M.C123_ABC...&lc=1033`
6. **Paste the URL** into the **"Manual Code"** field in the setup flow
7. Click **Submit**
8. Authentication completes automatically! ✅

**💡 Pro Tip:** The integration automatically extracts the code from the URL - you can paste the full URL or just the `code=` part.

#### Page 3: Console Discovery & Success!
After authentication, the integration will:
1. **Automatically discover** all Xbox consoles on your account (if Live ID was empty)
2. **Add all discovered consoles** to the configuration
3. Create **TWO entities** for the active console:
   - **Remote Control**: `remote.xbox_remote_[device_id]` - Full button control
   - **Media Player**: `media_player.xbox_[device_id]` - Gaming status display

**📝 Note:** v4.1.0 discovers all consoles but creates entities for the first one. Full multi-console UI support coming in v4.2.0!


## Using the Integration

### Remote Control Entity

The remote control entity provides complete Xbox dashboard navigation:

**Standard Controls:**
- **Power On/Off** - Control console power state
- **D-Pad Navigation** - Navigate Xbox dashboard
- **OK Button** - Mapped to A button (confirm/select)
- **Back Button** - Mapped to B button (cancel/back)
- **Home** - Return to Xbox home screen
- **Menu** - Context menu button
- **View** - Options/view button

**Media Controls:**
- **Play/Pause** - Control media playback
- **Stop** - Stop playback
- **Next/Previous** - Track navigation
- **Volume Up/Down** - TV volume via HDMI-CEC
- **Mute** - Mute TV via HDMI-CEC

**Button Mapping:**
- **DPAD_CENTER** → A Button (OK/Select)
- **BACK** → B Button (Cancel/Back)
- **HOME** → Xbox Home Button
- **MENU** → Menu Button
- **CONTEXT_MENU** → View Button
- **CHANNEL_UP** → Y Button
- **CHANNEL_DOWN** → X Button
- **Color Buttons** → Red (B), Green (A), Blue (X), Yellow (Y)

### Media Player Entity

The media player entity displays live Xbox gaming activity:

**Status Display:**
- **OFF** - Console is powered off or unreachable
- **ON** - Console is online, on dashboard/home screen
- **PLAYING** - Actively playing a game

**Information Shown:**
- **Media Title**: Current game title (when playing) or status
- **Gamertag**: Your Xbox Live gamertag
- **Game Artwork**: Official game cover art from Xbox Live
- **Activity State**: Real-time presence information

**Automatic Updates:**
- Status refreshes every 60 seconds
- Game changes detected automatically
- Presence updates in real-time
- No manual refresh needed

## Troubleshooting

### Power On Not Working

**Symptoms:** Cannot turn on Xbox console remotely

**Solutions:**
1. ✅ Verify console is in **Sleep** power mode (Settings → Power options)
2. ✅ Check that **Remote Features** are enabled on Xbox
3. ✅ Ensure console is on same network as Remote
4. ✅ Wait 30-60 seconds after console enters sleep before trying power on
5. ✅ Console may need to be turned on once manually after changing power mode

**Common Causes:**
- Console in "Energy Saving" mode instead of "Sleep"
- Remote features not enabled
- Console not connected to network
- First-time setup incomplete

### Authentication Failed - "unauthorized_client" Error

**Symptoms:** Setup fails with error: "The client does not have a secret configured"

**Most Common Cause:** Your Azure client secret contains special characters (`+`, `~`, `/`) that Microsoft's OAuth cannot handle

**Quick Fix:**
1. ✅ Go to Azure Portal → Your App → Certificates & secrets
2. ✅ Delete current client secret and generate a new one
3. ✅ Keep generating until you get a secret WITHOUT `+`, `~`, or `/` characters
4. ✅ Use the new secret in integration setup

📖 **[Detailed troubleshooting guide](TROUBLESHOOTING_SPECIAL_CHARS.md)**

### Authentication Failed - Other Issues

**Symptoms:** Setup fails during Microsoft login

**Solutions:**
1. ✅ Ensure you're using correct Microsoft account (linked to Xbox)
2. ✅ Copy the **entire** redirect URL including all parameters
3. ✅ Don't modify the URL - paste exactly as shown in browser
4. ✅ Clear browser cache and try again
5. ✅ Try incognito/private browsing mode

**Common Causes:**
- Wrong Microsoft account used
- Partial URL copied (missing parameters)
- Browser auto-completing/modifying URL
- Account doesn't have Xbox Live access

### Commands Not Responding

**Symptoms:** Remote buttons don't control console

**Solutions:**
1. ✅ Verify console is powered on and connected
2. ✅ Test Xbox app on phone to confirm console is reachable
3. ✅ Restart integration from Remote web configurator
4. ✅ Check integration logs for authentication errors
5. ✅ Re-authenticate if tokens expired (typically 90 days)

**Common Causes:**
- Console powered off or in Energy Saving mode
- Network connectivity issues
- Authentication tokens expired
- Xbox Live service issues

### Game Not Showing in Media Player

**Symptoms:** Media player shows "Home" but not current game

**Solutions:**
1. ✅ Wait up to 60 seconds for presence update
2. ✅ Verify game is actually running (not suspended)
3. ✅ Check that Xbox Live privacy settings allow presence sharing
4. ✅ Some games may not report detailed presence information

**Common Causes:**
- Game suspended in background
- Privacy settings restricting presence
- Update polling interval hasn't elapsed
- Game doesn't report to Xbox Live

### Volume Control Not Working

**Symptoms:** Volume buttons have no effect

**Explanation:**
Xbox controls TV volume via **HDMI-CEC** only. Commands are sent to TV through HDMI cable.

**Solutions:**
1. ✅ Enable HDMI-CEC on your TV:
   - Samsung: "Anynet+"
   - LG: "Simplink"  
   - Sony: "Bravia Sync"
   - Panasonic: "VIERA Link"
   - Philips: "EasyLink"
2. ✅ Verify HDMI cable connects Xbox to TV
3. ✅ Check TV settings for CEC/device control
4. ✅ Enable CEC per HDMI input on some TVs

**Common Causes:**
- HDMI-CEC disabled on TV
- Xbox connected through AV receiver/soundbar
- TV doesn't support CEC
- Wrong HDMI input selected

### Integration Logs

**Access Logs:**
- **Remote Interface**: Settings → Integrations → Xbox Integration → View Logs
- **Docker**: `docker logs uc-intg-xbox`

**Look For:**
- Authentication failures
- Token refresh errors  
- API communication issues
- Button command errors

## Known Limitations

### Xbox Live API Restrictions

- **No Media App Control** - Cannot control Netflix, YouTube, etc. (API security/DRM limitation)
- **Dashboard Only** - Full control works on dashboard, limited in third-party apps
- **Cloud-Based** - Commands sent via Xbox Live servers (requires internet)
- **Response Delays** - Some commands may have slight delay due to cloud routing

### Power Management

- **Sleep Mode Required** - Power on only works with Sleep mode, not Energy Saving
- **Manual First Start** - May need manual power on after initial setup
- **Network Requirement** - Console must maintain network connection in sleep

### Volume Control

- **HDMI-CEC Only** - Volume commands use TV's HDMI-CEC, not Xbox directly
- **TV Compatibility** - Requires CEC-compatible TV
- **Receiver Routing** - May not work if Xbox connected through AV receiver

### Authentication

- **Token Expiration** - OAuth tokens expire periodically (~90 days)
- **Re-authentication** - Will require re-setup when tokens expire
- **Internet Required** - Authentication requires active internet connection

## Advanced Configuration

### Custom Polling Intervals

Edit `config.json` in integration data directory:
```json
{
  "liveid": "YOUR_XBOX_LIVE_DEVICE_ID",
  "tokens": { ... },
  "polling_interval": 60
}
```

- **polling_interval**: Game presence update frequency in seconds (default: 60)

**Note:** Lower polling intervals increase API requests and may impact Xbox Live rate limits.

### Multiple Xbox Consoles

Currently, the integration supports **one Xbox console per installation**.

For multiple consoles, install separate integration instances:
1. Each instance connects to different console
2. Each instance requires separate authentication
3. Use Docker with different config paths for each instance
4. Each needs unique Xbox Live Device ID

## For Developers

### Local Development

1. **Clone and setup:**
```bash
   git clone https://github.com/mase1981/uc-intg-xbox.git
   cd uc-intg-xbox
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
```

2. **Configuration:**
```bash
   export UC_CONFIG_HOME=./config
```

3. **Run development:**
```bash
   python uc_intg_xbox/driver.py
```

4. **VS Code debugging:**
   - Open project in VS Code
   - Use F5 to start debugging session
   - Configure with real Xbox Live credentials

### Project Structure
```
uc-intg-xbox/
├── uc_intg_xbox/              # Main package
│   ├── __init__.py            # Package info  
│   ├── auth.py                # Xbox OAuth2 authentication
│   ├── config.py              # Configuration management
│   ├── driver.py              # Main integration driver
│   ├── xbox_client.py         # Xbox Web API client
│   ├── remote_entity.py       # Remote control entity
│   ├── media_player_entity.py # Media player entity
│   └── setup.py               # Setup wizard
├── .github/workflows/         # GitHub Actions CI/CD
│   └── build.yml              # Automated build pipeline
├── docker-compose.yml         # Docker deployment
├── Dockerfile                 # Container build instructions
├── driver.json                # Integration metadata
├── requirements.txt           # Dependencies
├── pyproject.toml             # Python project config
└── README.md                  # This file
```

### Key Implementation Details

#### **Xbox Live Web API Communication**
- Uses `xbox-webapi-python` library for Xbox Live API
- OAuth2 authentication via Microsoft identity platform
- Commands sent to `https://xccs.xboxlive.com/commands`
- Presence data from `https://peoplehub.xboxlive.com`
- Game metadata from `https://titlehub.xboxlive.com`

#### **Authentication Flow**
```python
# OAuth2 with authorization code flow
1. Generate authorization URL
2. User authenticates with Microsoft
3. Receive authorization code from redirect
4. Exchange code for access/refresh tokens
5. Store tokens for future use
6. Auto-refresh every 12 hours
```

#### **Entity Architecture**
- **Remote Entity**: Full button control via `InputKeyType` enums
- **Media Player Entity**: Read-only presence display
- Independent command handlers per entity
- Remote uses Xbox SmartGlass API endpoints
- Media player polls Xbox Live presence API

#### **Presence Detection**
```python
# Presence update flow
1. Call get_friends_own_batch([xuid])
2. Extract presence_details from response
3. Check for Active game with is_primary=True
4. Fetch title_info for game metadata
5. Update media player attributes
6. Repeat every 60 seconds
```

#### **Reboot Survival Pattern**
```python
# Pre-initialize entities if config exists
if config.is_configured():
    asyncio.create_task(_initialize_entities())

# Reload config on reconnect
async def on_connect():
    config.reload_from_disk()
    if not entities_ready:
        await _initialize_entities()
```

### Xbox Web API Reference

Essential API endpoints used by this integration:

**SmartGlass Commands:**
```python
# Power control
client.smartglass.wake_up(live_id)
client.smartglass.turn_off(live_id)

# Button presses
client.smartglass.press_button(live_id, InputKeyType.A)
client.smartglass.press_button(live_id, InputKeyType.Home)

# Volume control (HDMI-CEC)
client.smartglass.change_volume(live_id, VolumeDirection.Up)
client.smartglass.mute(live_id)

# Console status
client.smartglass.get_console_status(live_id)
```

**Presence API:**
```python
# Get user presence
client.people.get_friends_own_batch([xuid])

# Get game title info
client.titlehub.get_title_info(title_id)
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test with real Xbox console
4. Commit changes: `git commit -m 'Add amazing feature'`
5. Push to branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

### Code Style

- Follow PEP 8 Python conventions
- Use type hints for all functions
- Async/await for all I/O operations
- Comprehensive docstrings
- Descriptive variable names

## Credits

- **Developer**: Meir Miyara
- **xbox-webapi-python**: [OpenXbox/xbox-webapi-python](https://github.com/OpenXbox/xbox-webapi-python)
- **Unfolded Circle**: Remote 2/3 integration framework (ucapi)
- **Reference Integrations**: PSN and JVC integrations by Jack Powell
- **Community**: Testing and feedback from UC community

## License

This project is licensed under the Mozilla Public License 2.0 (MPL-2.0) - see LICENSE file for details.
```
Copyright (c) 2025 Meir Miyara

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
```

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-xbox/issues)
- **GitHub Discussions**: [General discussion and support](https://github.com/mase1981/uc-intg-xbox/discussions)
- **UC Community Forum**: [Unfolded Circle community](https://community.unfoldedcircle.com/)
- **Discord**: [Unfolded Circle Discord](https://discord.gg/zGVYf58)
- **Developer**: [Meir Miyara](https://github.com/mase1981)

---

**Made with ❤️ for the Unfolded Circle and Xbox Gaming Communities** 

**Enjoy controlling your Xbox with your Unfolded Circle Remote!** 🎮

**Thank You**: Meir Miyara