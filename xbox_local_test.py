"""Does the Xbox still answer the local SmartGlass protocol (UDP 5050) on this network?

Stage 1 - discovery (Python standard library only):

    python xbox_local_test.py --ip 192.168.1.50

    Sends the SmartGlass discovery request to the console and prints its answer.
    No answer = the console does not offer local SmartGlass (or a firewall blocks
    UDP 5050), and stage 2 is pointless.

Stage 2 - which app has focus, live (only if stage 1 answered):

    Needs the archived open-source library, best in its own virtual environment:
        python -m venv sgtest
        sgtest\\Scripts\\activate
        pip install xbox-smartglass-core
        python xbox_local_test.py --ip 192.168.1.50 --connect --minutes 10

    Prints every console status message: each running title, whether it has
    focus, and its app id. Switch between a game and Home while it runs.

The console's IP is in Xbox Settings > General > Network settings > Advanced settings.
"""

import argparse
import asyncio
import socket
import struct
import sys
import time
from datetime import datetime

PORT = 5050
DISCOVERY_REQUEST = 0xDD00
DISCOVERY_RESPONSE = 0xDD01
CLIENT_TYPE_ANDROID = 8


def log(text: str) -> None:
    line = f"{datetime.now():%H:%M:%S}  {text}"
    print(line)
    with open("xbox_local_log.txt", "a", encoding="utf-8") as file:
        file.write(line + "\n")


def discovery_request() -> bytes:
    """SmartGlass discovery request: header (type, payload length, version) + payload."""
    payload = struct.pack(">IHHH", 0, CLIENT_TYPE_ANDROID, 0, 2)  # flags, client type, min/max version
    return struct.pack(">HHH", DISCOVERY_REQUEST, len(payload), 0) + payload


def _sg_string(data: bytes, offset: int) -> tuple[str, int]:
    length = struct.unpack_from(">H", data, offset)[0]
    offset += 2
    text = data[offset:offset + length].decode("utf-8", "replace")
    return text, offset + length + 1  # strings end with a null byte


def parse_response(data: bytes) -> dict:
    pkt_type, _length, _version = struct.unpack_from(">HHH", data, 0)
    if pkt_type != DISCOVERY_RESPONSE:
        return {"type": hex(pkt_type)}
    flags, device_type = struct.unpack_from(">IH", data, 6)
    name, offset = _sg_string(data, 12)
    uuid, offset = _sg_string(data, offset)
    last_error = struct.unpack_from(">I", data, offset)[0]
    cert_len = struct.unpack_from(">H", data, offset + 4)[0]
    return {
        "type": "discovery response",
        "name": name,
        "uuid": uuid,
        "flags": hex(flags),
        "device_type": device_type,
        "last_error": last_error,
        "certificate_bytes": cert_len,
    }


def discover(ip: str, tries: int = 5) -> bool:
    log(f"=== stage 1: SmartGlass discovery to {ip}:{PORT} (UDP)")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(1.0)
        for attempt in range(1, tries + 1):
            sock.sendto(discovery_request(), (ip, PORT))
            try:
                data, addr = sock.recvfrom(4096)
            except socket.timeout:
                log(f"  try {attempt}: no answer")
                continue
            try:
                info = parse_response(data)
            except Exception as err:  # noqa: BLE001
                info = {"unparsed_bytes": len(data), "error": str(err)}
            log(f"  answer from {addr[0]}: {info}")
            return True
    log("  The console did not answer. Local SmartGlass is off or blocked; stage 2 cannot work.")
    return False


async def watch_focus(ip: str, minutes: float) -> None:
    """Connect anonymously with xbox-smartglass-core and print console status messages."""
    log("=== stage 2: connect and watch which app has focus")
    try:
        from xbox.sg.console import Console  # type: ignore[import-not-found]
    except ImportError:
        log("  xbox-smartglass-core is not installed (see the instructions at the top of this file).")
        return

    try:
        consoles = await Console.discover(addr=ip, timeout=3)
    except TypeError:
        consoles = await Console.discover(addr=ip)
    if not consoles:
        log("  Library discovery found no console.")
        return
    console = consoles[0]
    log(f"  found {getattr(console, 'name', '?')}, connecting (anonymous)...")

    def on_status(status) -> None:
        titles = getattr(status, "active_titles", None) or []
        rows = []
        for title in titles:
            rows.append(
                f"title_id={getattr(title, 'title_id', '?')} "
                f"focus={getattr(title, 'has_focus', '?')} "
                f"aum={getattr(title, 'aum', '?')!r}"
            )
        log("  status: " + (" | ".join(rows) if rows else repr(status)))

    try:
        console.on_console_status += on_status
    except Exception as err:  # noqa: BLE001
        log(f"  could not subscribe to status: {err}")
    try:
        state = await console.connect(userhash="", xsts_token="")
    except Exception as err:  # noqa: BLE001
        log(f"  connect failed: {type(err).__name__}: {err}")
        log("  On the Xbox: Settings > Devices & connections > Remote features > Xbox app preferences >")
        log("  'Allow connections from any device', then try again.")
        return
    log(f"  connect result: {state}")
    end = time.monotonic() + minutes * 60
    while time.monotonic() < end:
        await asyncio.sleep(1)
    try:
        await console.disconnect()
    except Exception:  # noqa: BLE001
        pass
    log("=== stage 2 end")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", required=True, help="the console's IP address")
    parser.add_argument("--connect", action="store_true", help="stage 2: connect and watch focus")
    parser.add_argument("--minutes", type=float, default=10)
    args = parser.parse_args()

    if not discover(args.ip):
        sys.exit(1)
    if args.connect:
        asyncio.run(watch_focus(args.ip, args.minutes))


if __name__ == "__main__":
    main()
