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

#### Method 1: Mobile/Desktop App (Recommended)

1. Go to https://portal.azure.com
2. Navigate to **Microsoft Entra ID** → **App registrations**
3. Click **"+ New registration"**
<img width="1052" height="383" alt="image" src="https://github.com/user-attachments/assets/4ae080ba-254c-4f84-b9e0-05e56d4a5b0b" />
<img width="393" height="417" alt="image" src="https://github.com/user-attachments/assets/09f4cef3-eded-4874-89cc-df8f22b203c2" />

5. Fill in:
   - **Name**: `Unfolded Circle Xbox Integration`
   - **Supported accounts**: Select **"Accounts in any organizational directory (Any Microsoft Entra ID tenant - Multitenant) and personal Microsoft accounts (e.g. Skype, Xbox)"**
6. Click **"Register"** (don't add redirect URI yet)
<img width="681" height="363" alt="image" src="https://github.com/user-attachments/assets/8ca1d6e4-06cd-423f-87c4-3644af22a155" />

8. Copy your **Application (client) ID**
<img width="587" height="269" alt="image" src="https://github.com/user-attachments/assets/94cce609-d7ae-4d2f-aff0-172cf953f1a9" />

10. Click **Authentication** → **Add a platform** → Select **"Mobile and desktop applications"**
<img width="1275" height="515" alt="image" src="https://github.com/user-attachments/assets/32cac6d5-efdc-49d1-80e5-7f87b40374f3" />

12. In **Custom redirect URIs**, enter: `http://localhost:8765/callback`
13. Click **Register**
<img width="1048" height="306" alt="image" src="https://github.com/user-attachments/assets/71ae53d6-7c12-465f-af60-2b371613bd82" />

14. Click on **Settings** → Set **"Allow public client flows"** to **YES**
15. Click **Save**

<img width="288" height="179" alt="image" src="https://github.com/user-attachments/assets/4222f653-3abc-437e-bfde-04f6afadc14b" />

16. During integration setup, **LEAVE THE CLIENT SECRET FIELD EMPTY** (don't enter anything)

**Note:** This method works for most users and doesn't require managing a client secret.

#### Method 2: Web App (Alternative)

If you prefer using a client secret or Method 1 doesn't work:
1. Go to https://portal.azure.com
2. Navigate to **Microsoft Entra ID** → **App registrations**
3. Click **"+ New registration"**
4. Fill in:
   - **Name**: `Unfolded Circle Xbox Integration`
   - **Supported accounts**: Select **"Accounts in any organizational directory (Any Microsoft Entra ID tenant - Multitenant) and personal Microsoft accounts (e.g. Skype, Xbox)"**
5. Click **"Register"** (don't add redirect URI yet)
6. Copy your **Application (client) ID**
7. Click **Authentication** → **Add a platform** → Select **"Web"**
8. Enter redirect URI: `http://localhost:8765/callback`
9. Click **Configure**
10. Go to **Certificates & secrets** → Click **"+ New client secret"**
11. Add description, choose expiration (24 months recommended)
12. Click **Add** and immediately copy the **Secret VALUE** (not the Secret ID)
13. Save both Client ID and Secret for setup

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
- **UC Community Forum**: [Unfolded Circle community](https://unfolded.community/)
- **Discord**: [Unfolded Circle Discord](https://discord.gg/zGVYf58)
- **Developer**: [Meir Miyara](https://github.com/mase1981)

---

**Made with ❤️ for the Unfolded Circle and Xbox Gaming Communities** 

**Enjoy controlling your Xbox with your Unfolded Circle Remote!** 🎮

**Thank You**: Meir Miyara
