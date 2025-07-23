# Unfolded Circle Xbox Integration

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Disclaimer:** This is my first contribution to the unfolded circle community, truly hope it works out for you, Thank You: Meir Miyara

This is a custom integration for the Unfolded Circle Remote that allows you to control your Xbox One, Xbox Series S, or Xbox Series X console.

This integration allows for remote control of your console's dashboard, including power, navigation, volume, and media playback controls directly from your Unfolded Circle remote.

## Features

* **Power On/Off**: Turn your console on and off.
* **Dashboard Control**: Full navigation with D-Pad and system buttons on the main Xbox dashboard.
* **Volume Control**: Control the volume of your TV or AV receiver (via CEC if configured on your Xbox).
* **Media Controls**: Play, Pause, and skip tracks on the Xbox dashboard.
* **Authentication**: Secure OAuth2-based authentication with your Microsoft account.
* **Auto-Discovery**: The integration is discoverable by the Unfolded Circle remote on your network.

## Known Limitations

* **No In-App Control for Media Apps:** This integration provides full control over the main Xbox dashboard. However, it **cannot** control third-party media applications (like Netflix, YouTube, etc.) once they are launched. This is a limitation of the public Xbox Web API, as most media apps are designed to ignore these types of remote commands for security and DRM reasons.

## IMPORTANT: Prerequisites

1.  An Unfolded Circle Remote (RC2 or RC3).
2.  An Xbox One, Xbox Series S, or Xbox Series X console.
3.  Your Xbox must be set to **Sleep** power mode (previously "Instant-on") for Power On to function. You can find this in `Settings > General > Power options`.
4.  You must enable remote features on your Xbox. To do this, go to `Settings > Devices & connections > Remote features` and check the box for "Enable remote features".
5.  You will need your console's **Xbox Live Device ID**, which is found on that same settings page.
6.  Your remote and xBox console **must** be on the same network.
7.  It is ideal for both remote and xBox to have static IP. 
8.  As integration rely on internet connection, some responses will be delayed - especially if remote sleep settings are set to low value (eg: 30 seconds)

## Installation

There are two recommended ways to install and run this integration:

### Method 1: Docker (Recommended)

This is the easiest way to run the integration. This method works on any machine that runs Docker, such as a home server or a Synology NAS.

1.  **Clone or download** the project files from this GitHub repository.

2.  **Configure the Docker Host IP Address.** To ensure auto-discovery works correctly, you must provide the integration with the IP address of the machine Docker is running on (e.g., your Synology NAS).
    * Open the `docker-compose.yml` file in a text editor.
    * Find the line that says `UC_MDNS_LOCAL_HOSTNAME=YOUR_NAS_IP_ADDRESS_HERE`.
    * Replace `YOUR_NAS_IP_ADDRESS_HERE` with the actual local IP address of your NAS/server.

3.  **Start the integration.** From a terminal in the project's root directory, run the following command:

    ```bash
    docker-compose up --build -d
    ```

The integration will build and start in the background. It is now ready to be added on your remote via auto-discovery.

#### Alternative Docker Commands
** Please read Docker instructions carefully **
If you don't have `docker-compose` installed, you can use these standard Docker commands instead.

1.  **Build the image:**
    ```bash
    docker build -t uc-intg-xbox .
    ```
2.  **Run the container.** **Important:** Replace `YOUR_NAS_IP_ADDRESS_HERE` in the command below with the actual IP address of your Docker host machine.
    ```bash
    # For PowerShell, Linux, or macOS
    docker run -d --name uc-intg-xbox --network host -e "UC_MDNS_LOCAL_HOSTNAME=YOUR_NAS_IP_ADDRESS_HERE" -v "$(pwd)/config:/config" --restart unless-stopped uc-intg-xbox

    # For Windows Command Prompt (cmd.exe)
    docker run -d --name uc-intg-xbox --network host -e "UC_MDNS_LOCAL_HOSTNAME=YOUR_NAS_IP_ADDRESS_HERE" -v "%cd%/config:/config" --restart unless-stopped uc-intg-xbox
    ```

### Method 2: Manual Installation (`.tar.gz`)

You can install the integration directly onto your Unfolded Circle remote.

1.  Download the latest release `.tar.gz` file from the [releases page](https://github.com/mase1-nase1/uc-intg-xbox/releases) of this repository.
2.  Open your Unfolded Circle web configurator in a browser (`http://<your_remote_ip>`).
3.  Navigate to `Settings > System > Integrations`.
4.  Click the `+` button and select `Upload a custom integration`.
5.  Select the `.tar.gz` file you downloaded.

## READ CAREFULLY: Configuration

After the integration is installed and running, you need to add it on your remote:

1.  On the Unfolded Circle remote or in the web configurator, go to "Integrations".
2.  Click on "Add New", find the "Xbox Integration" - you might need to wait a second if you are using Docker as it will show as "External"
3.  You will be prompted to enter your **Xbox Live Device ID**. Enter the ID you found in the prerequisites and click Next.
4.  The Web Configurator will display a URL and a field to paste a redirected URL.
5.  Copy the login URL (make sure to copy the entire URL) and open it in a web browser/Tab. Log in with the Microsoft account associated with your Xbox.
6.  After successful login, you will be redirected to a blank page. **Copy the entire URL** from your browser's address bar.
7.  Paste this full URL back into the "Paste the full redirect URL here" field on your remote and complete the setup.
8.  **Manually Add the Remote Entity (If Needed):** If the "Xbox Remote" entity doesn't appear automatically, go to the xBox Integration's settings page, find "Configured Entities," and tap "Add" next to the Xbox Remote.
9.  The Xbox entity is now ready to use!

## Development

Interested in contributing? Here’s how to set up a development environment.

1.  Clone the repository:
    ```bash
    git clone [https://github.com/mase1981/uc-intg-xbox.git](https://github.com/mase1981/uc-intg-xbox.git)
    cd uc-intg-xbox
    ```
2.  Create and activate a Python virtual environment. Python 3.10 or higher is required.
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use .venv\Scripts\activate
    ```
3.  Install the project in editable mode with its dependencies:
    ```bash
    pip install -e .
    ```
4.  Run the driver:
    ```bash
    python -m uc_intg_xbox.driver
    ```

## License

This project is licensed under the MIT License.

## Acknowledgements

* This project is powered by the [xbox-webapi](https://github.com/OpenXbox/xbox-webapi-python) library.
* Special thanks to the [Unfolded Circle](https://www.unfoldedcircle.com/) team for creating a remote with an open API.
* Thanks to [Jack Powell](https://github.com/JackJPowell) for the PSN and JVC integrations which served as excellent reference point and help with local build.
* Thanks to (Mike Hobin) (https://github.com/mikehobin) for the help with the container proper configuration.