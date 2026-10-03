"""Xbox probe: shows what your console and Xbox Live report, every 10 seconds.

Run from the repository root (needs the integration's requirements installed):

    pip install -r requirements.txt
    python xbox_probe.py --client-id YOUR_AZURE_CLIENT_ID [--client-secret SECRET] [--minutes 10]
        [--liveid YOUR_XBOX_LIVE_DEVICE_ID] [--fresh]

--liveid skips the console list (the Device ID from Xbox Settings > Devices &
connections > Remote features). --fresh forgets the saved sign-in.

While it runs: play a game, go back to Home, start another game, open an app.
It prints a line only when something changes, and writes the same to
xbox_probe_log.txt. Send that file back. It contains no tokens, gamertag or IDs
of your account; the console ID is shortened.

Sign-in is cached in xbox_probe_tokens.json (keep that file private, delete it
when done).
"""

import argparse
import asyncio
import json
import os
import sys
import time
import webbrowser
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from uc_intg_xbox.client import XboxClient  # noqa: E402
from uc_intg_xbox.oauth_server import OAuthCallbackServer  # noqa: E402
from uc_intg_xbox.setup_flow import _extract_code  # noqa: E402

TOKENS_FILE = "xbox_probe_tokens.json"
LOG_FILE = "xbox_probe_log.txt"


def log(text: str) -> None:
    line = f"{datetime.now():%H:%M:%S}  {text}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(line + "\n")


async def sign_in(client_id: str, client_secret: str) -> XboxClient:
    client = XboxClient(client_id, client_secret)
    if os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, encoding="utf-8") as file:
            tokens = json.load(file)
        try:
            refreshed = await client.connect(tokens)
            _save(refreshed)
            return client
        except Exception as err:  # noqa: BLE001
            print(f"Saved sign-in did not work ({err}); signing in again.")
            await client.close()
            client = XboxClient(client_id, client_secret)

    url = client.generate_auth_url()
    server = OAuthCallbackServer()
    try:
        await server.start()
    except Exception:  # noqa: BLE001
        server = None
    print("\nSign in with the Microsoft account linked to your Xbox:\n" + url + "\n")
    webbrowser.open(url)
    code = await server.wait_for_code(timeout=180) if server else None
    if server:
        await server.stop()
    if not code:
        pasted = input("Paste the address you landed on after signing in: ").strip()
        code = _extract_code(pasted)
    tokens = await client.exchange_code(code)
    await client.close()
    client = XboxClient(client_id, client_secret)
    _save(await client.connect(tokens))
    return client


def _save(tokens: dict | None) -> None:
    if tokens:
        with open(TOKENS_FILE, "w", encoding="utf-8") as file:
            json.dump(tokens, file)


def _details(person) -> list[str]:
    out = []
    for d in getattr(person, "presence_details", None) or []:
        out.append(
            f"[state={d.state} game={d.is_game} primary={d.is_primary} title_id={d.title_id} "
            f"device={d.device} text={d.presence_text!r}]"
        )
    return out


async def snapshot(client: XboxClient, liveid: str, names: dict) -> dict:
    """Everything each source reports right now (errors included)."""
    raw = client._client  # pylint: disable=protected-access
    snap: dict = {}

    try:
        status = await raw.smartglass.get_console_status(liveid)
        aumid = status.focus_app_aumid or ""
        snap["console"] = f"power={status.power_state} playback={status.playback_state} focus={aumid!r}"
        app = await client._app_details(aumid) if aumid else None  # pylint: disable=protected-access
        snap["catalog"] = f"title={((app or {}).get('title') or '')!r} is_game={(app or {}).get('is_game')}"
    except Exception as err:  # noqa: BLE001
        snap["console"] = f"ERROR {type(err).__name__}: {err}"
        app = None

    # Source of the Status sensor and of 5.3.3's title
    try:
        response = await raw.people.get_friend_by_xuid(client.xuid)
        person = (response.people or [None])[0]
        snap["profile"] = (
            f"state={person.presence_state} text={person.presence_text!r} " + " ".join(_details(person))
            if person else "no person"
        )
    except Exception as err:  # noqa: BLE001
        snap["profile"] = f"ERROR {type(err).__name__}: {err}"

    # Source of 5.2.9's title
    try:
        response = await raw.people.get_friends_own_batch([client.xuid])
        person = next((p for p in response.people or [] if p.xuid == client.xuid), None)
        snap["presence_batch"] = (
            f"state={person.presence_state} text={person.presence_text!r} " + " ".join(_details(person))
            if person else "no person"
        )
    except Exception as err:  # noqa: BLE001
        snap["presence_batch"] = f"ERROR {type(err).__name__}: {err}"

    # What each version would show as the current game
    try:
        presence = await client.get_presence(liveid)
        snap["5.2.9 shows"] = repr((presence or {}).get("title"))
    except Exception as err:  # noqa: BLE001
        snap["5.2.9 shows"] = f"ERROR {err}"
    try:
        profile = await client.get_profile()
        title = (app or {}).get("title")
        if not title and profile and profile.get("online"):
            title_id = profile.get("title_id")
            if title_id and title_id not in names:
                info = await client.get_title_progress(title_id)
                names[title_id] = (info or {}).get("name") or ""
            title = names.get(title_id) if title_id else None
            title = title or profile.get("status")
        snap["5.3.3 shows"] = repr(title or "")
    except Exception as err:  # noqa: BLE001
        snap["5.3.3 shows"] = f"ERROR {err}"
    return snap


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--client-secret", default="")
    parser.add_argument("--minutes", type=float, default=10)
    parser.add_argument("--liveid", default="")
    parser.add_argument("--fresh", action="store_true")
    args = parser.parse_args()

    if args.fresh and os.path.exists(TOKENS_FILE):
        os.remove(TOKENS_FILE)
    client = await sign_in(args.client_id, args.client_secret)
    try:
        # Shown on screen only (not in the log file), to check the right account signed in.
        print(f"\nSigned in as gamertag: {client.gamertag}\n")
        liveid = args.liveid.strip()
        name = "console"
        if not liveid:
            try:
                consoles = await client.get_consoles()
            except Exception as err:  # noqa: BLE001
                print(f"Console list failed: {type(err).__name__}: {err}")
                consoles = []
            if not consoles:
                print(
                    "No consoles found for this account. If that gamertag is not yours, run again with "
                    "--fresh and sign in with the account linked to your Xbox (use a private browser "
                    "window if the browser signs in automatically). Or pass --liveid YOUR_DEVICE_ID."
                )
                return
            console = consoles[0]
            if len(consoles) > 1:
                for index, item in enumerate(consoles, 1):
                    print(f"{index}. {item['name']}")
                console = consoles[int(input("Console number: ")) - 1]
            liveid, name = console["id"], console["name"]
        log(f"=== probe start, {name} ({liveid[:4]}…), every 10 s for {args.minutes:g} min")

        last: dict = {}
        names: dict = {}
        end = time.monotonic() + args.minutes * 60
        while time.monotonic() < end:
            snap = await snapshot(client, liveid, names)
            changed = {key: value for key, value in snap.items() if last.get(key) != value}
            if changed:
                log("-" * 60)
                for key, value in snap.items():
                    log(f"{'*' if key in changed else ' '} {key:15} {value}")
            last = snap
            await asyncio.sleep(10)
        log("=== probe end")
    finally:
        await client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped. Send xbox_probe_log.txt")
