# Xbox Integration for Unfolded Circle Remote 2/3

Control your Xbox One, Xbox Series S, or Xbox Series X console with the Unfolded Circle Remote 2 or Remote 3 with **comprehensive dashboard navigation**, **power management**, **currently playing game display**, and **media playback control** directly from your remote.

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

This integration provides comprehensive control of your Xbox console through the Xbox Live Web API, delivering seamless integration with your Unfolded Circle Remote for complete gaming control, live status display with game artwork, and full remote navigation.

---
## ❤️ Support Development ❤️

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
- **Automatic Updates** - Status refreshes every 60 seconds

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

### **Supported Consoles**

- **Xbox One** (Original, S, X)
- **Xbox Series S**
- **Xbox Series X**

### **Protocol Requirements**

- **Protocol**: Xbox Live Web API
- **Microsoft Account**: With Xbox Live access
- **Xbox Live Device ID**: Found in console settings
- **Remote Features**: Must be enabled on console
- **Sleep Power Mode**: Required for remote power on functionality
- **Internet Connectivity**: Console must be connected to internet

### **Network Requirements**

- **Internet Access** - Required for Xbox Live API communication
- **HTTPS Protocol** - Integration uses secure HTTPS to Xbox Live servers
- **Firewall** - Ensure outbound HTTPS traffic is permitted
- **Local Network** - Remote and Xbox should be on same network for best performance

## Installation

### Option 1: Remote Web Interface (Recommended)
1. Navigate to the [**Releases**](https://github.com/mase1981/uc-intg-xbox/releases) page
2. Download the latest `uc-intg-xbox-<version>-aarch64.tar.gz` file
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
      - UC_INTEGRATION_INTERFACE=0.0.0.0
      - PYTHONPATH=/app
    restart: unless-stopped
```

**Docker Run:**
```bash
docker run -d --name uc-intg-xbox --restart unless-stopped --network host -v xbox-config:/data -e UC_CONFIG_HOME=/data -e UC_INTEGRATION_INTERFACE=0.0.0.0 -e UC_INTEGRATION_HTTP_PORT=9094 -e PYTHONPATH=/app ghcr.io/mase1981/uc-intg-xbox:latest
```

## Configuration

### Step 1: Create Azure App Registration

**IMPORTANT**: Starting with version 4.0.0, due to Microsoft OAuth changes, you must create your own Azure App Registration.

#### Method 1: Mobile/Desktop App (Recommended)

1. Go to https://portal.azure.com
2. Navigate to **Microsoft Entra ID** → **App registrations**
3. Click **"+ New registration"**
4. Fill in:
   - **Name**: `Unfolded Circle Xbox Integration`
   - **Supported accounts**: Select **"Accounts in any organizational directory (Any Microsoft Entra ID tenant - Multitenant) and personal Microsoft accounts (e.g. Skype, Xbox)"**
5. Click **"Register"** (don't add redirect URI yet)
6. Copy your **Application (client) ID**
7. Click **Authentication** → **Add a platform** → Select **"Mobile and desktop applications"**
8. In **Custom redirect URIs**, enter: `http://localhost:8765/callback`
9. Click **Register**
10. Click on **Settings** → Set **"Allow public client flows"** to **YES**
11. Click **Save**
12. During integration setup, **LEAVE THE CLIENT SECRET FIELD EMPTY** (don't enter anything)

**Note:** This method works for most users and doesn't require managing a client secret.

#### Method 2: Web App (Alternative)

If you prefer using a client secret or Method 1 doesn't work:
1. Follow steps 1-6 from Method 1
2. Click **Authentication** → **Add a platform** → Select **"Web"**
3. Enter redirect URI: `http://localhost:8765/callback`
4. Click **Configure**
5. Go to **Certificates & secrets** → Click **"+ New client secret"**
6. Add description, choose expiration (24 months recommended)
7. Click **Add** and immediately copy the **Secret VALUE** (not the Secret ID)
8. Save both Client ID and Secret for setup

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
- **Azure App Client Secret**:
  - **If using Method 1 (Mobile/Desktop)**: Leave this field EMPTY
  - **If using Method 2 (Web)**: Paste your Client Secret Value
- **Number of Consoles**: Enter how many Xbox consoles you want to configure
- Click **Next**

#### Page 2: Console Details
- For each console, enter:
  - **Console Name**: Friendly name (e.g., "Living Room Xbox")
  - **Xbox Live Device ID**: Found in Xbox Settings → Devices & connections → Remote features
- Click **Next**

#### Page 3: Microsoft Authentication
The integration uses a **hybrid authentication** system with automatic callback + manual fallback:

**Steps:**
1. **Click the Authorization URL** (opens in your browser)
2. **Sign in** with your Microsoft account (the one linked to your Xbox)
3. After signing in, Microsoft will redirect to `http://localhost:8765/callback?code=...`
4. **The page won't load** (this is normal - the server is on the Remote, not your computer)
5. **Copy the entire URL** from your browser's address bar
6. **Paste the URL** into the **"Manual Code"** field in the setup flow
7. Click **Submit**
8. Authentication completes automatically

#### Page 4: Console Discovery & Success
After authentication, the integration will:
1. **Automatically discover** all Xbox consoles on your account (if Live ID was empty)
2. **Add all discovered consoles** to the configuration
3. Create **TWO entities** for each console:
   - **Remote Control**: Full button control
   - **Media Player**: Gaming status display

## Using the Integration

### Remote Control Entity

The remote control entity provides complete Xbox dashboard navigation:

- **Power On/Off** - Control console power state
- **D-Pad Navigation** - Navigate Xbox dashboard
- **OK Button** - Mapped to A button (confirm/select)
- **Back Button** - Mapped to B button (cancel/back)
- **Home** - Return to Xbox home screen
- **Menu** - Context menu button
- **View** - Options/view button
- **Media Controls** - Play/Pause, Stop, Next/Previous
- **Volume Up/Down** - TV volume via HDMI-CEC

### Media Player Entity

The media player entity displays live Xbox gaming activity:

- **Status Display**: OFF (powered off), ON (dashboard), PLAYING (in-game)
- **Media Title**: Current game title or status
- **Gamertag**: Your Xbox Live gamertag
- **Game Artwork**: Official game cover art from Xbox Live
- **Activity State**: Real-time presence information
- **Automatic Updates**: Status refreshes every 60 seconds

## Credits

- **Developer**: Meir Miyara
- **xbox-webapi-python**: [OpenXbox/xbox-webapi-python](https://github.com/OpenXbox/xbox-webapi-python)
- **Unfolded Circle**: Remote 2/3 integration framework (ucapi)
- **Protocol**: Xbox Live Web API
- **Community**: Testing and feedback from UC community

## License

This project is licensed under the Mozilla Public License 2.0 (MPL-2.0) - see LICENSE file for details.

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-xbox/issues)
- **GitHub Discussions**: [General discussion and support](https://github.com/mase1981/uc-intg-xbox/discussions)
- **UC Community Forum**: [Unfolded Circle community](https://unfolded.community/)
- **Discord**: [Unfolded Circle Discord](https://discord.gg/zGVYf58)
- **Developer**: [Meir Miyara](https://github.com/mase1981)

---

**Made with ❤️ for the Unfolded Circle and Xbox Gaming Communities**

**Thank You**: Meir Miyara
