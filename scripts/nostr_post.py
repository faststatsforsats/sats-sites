#!/usr/bin/env python3
"""Post the chart of the day to Nostr as the site's account.

    python3 scripts/nostr_post.py --dry-run          print the note, sign nothing, send nothing
    python3 scripts/nostr_post.py                    sign with NOSTR_NSEC and publish to the relays below
    python3 scripts/nostr_post.py --self-test        check the key handling and signing against known vectors

The note (kind 1, NIP-01) carries the chart's finding, the chart page's address, and the image address,
under 300 characters, as the style guide asks. The chart rotates through charts/index.json by the day of
the year, so each chart gets its turn about once a week.

Needs: coincurve (BIP-340 Schnorr signatures) and websockets. Both are in requirements-daily.txt.
The private key is read from the NOSTR_NSEC environment variable (nsec1... or 64 hex characters) and never
written anywhere.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "charts" / "index.json"
SITE = "https://faststatsforsats.com"
RELAYS = [
    "wss://relay.damus.io",
    "wss://nos.lol",
    "wss://relay.primal.net",
    "wss://relay.nostr.band",
    "wss://nostr.wine",
]

# ---------------------------------------------------------------- bech32 (BIP-173), for nsec/npub

CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def _polymod(values):
    gen = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
    chk = 1
    for v in values:
        b = chk >> 25
        chk = ((chk & 0x1FFFFFF) << 5) ^ v
        for i in range(5):
            chk ^= gen[i] if ((b >> i) & 1) else 0
    return chk


def _hrp_expand(hrp):
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def bech32_decode(text: str) -> tuple[str, bytes]:
    text = text.strip().lower()
    if "1" not in text:
        raise ValueError("not bech32")
    hrp, data = text.rsplit("1", 1)
    values = [CHARSET.index(c) for c in data]
    if _polymod(_hrp_expand(hrp) + values) != 1:
        raise ValueError("bad bech32 checksum")
    bits, acc, out = 0, 0, bytearray()
    for v in values[:-6]:
        acc = (acc << 5) | v
        bits += 5
        while bits >= 8:
            bits -= 8
            out.append((acc >> bits) & 0xFF)
    return hrp, bytes(out)


def bech32_encode(hrp: str, payload: bytes) -> str:
    bits, acc, values = 0, 0, []
    for byte in payload:
        acc = (acc << 8) | byte
        bits += 8
        while bits >= 5:
            bits -= 5
            values.append((acc >> bits) & 31)
    if bits:
        values.append((acc << (5 - bits)) & 31)
    poly = _polymod(_hrp_expand(hrp) + values + [0] * 6) ^ 1
    checksum = [(poly >> 5 * (5 - i)) & 31 for i in range(6)]
    return hrp + "1" + "".join(CHARSET[v] for v in values + checksum)


# ---------------------------------------------------------------- keys and events

def secret_key_bytes(secret: str) -> bytes:
    secret = secret.strip()
    if secret.startswith("nsec1"):
        hrp, raw = bech32_decode(secret)
        if hrp != "nsec" or len(raw) != 32:
            raise ValueError("not an nsec key")
        return raw
    raw = bytes.fromhex(secret)
    if len(raw) != 32:
        raise ValueError("a hex secret key has 64 characters")
    return raw


def public_key_hex(secret: bytes) -> str:
    from coincurve import PrivateKey

    return PrivateKey(secret).public_key.format(compressed=True)[1:].hex()


def event_id(pubkey: str, created_at: int, kind: int, tags: list, content: str) -> str:
    serialized = json.dumps([0, pubkey, created_at, kind, tags, content], separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def sign_event(secret: bytes, kind: int, content: str, tags: list, created_at: int | None = None) -> dict:
    from coincurve import PrivateKey

    pubkey = public_key_hex(secret)
    created_at = created_at or int(dt.datetime.now(dt.timezone.utc).timestamp())
    eid = event_id(pubkey, created_at, kind, tags, content)
    signature = PrivateKey(secret).sign_schnorr(bytes.fromhex(eid), aux_randomness=b"").hex()
    return {"id": eid, "pubkey": pubkey, "created_at": created_at, "kind": kind, "tags": tags, "content": content, "sig": signature}


def verify_event(event: dict) -> bool:
    from coincurve import PublicKeyXOnly

    expected = event_id(event["pubkey"], event["created_at"], event["kind"], event["tags"], event["content"])
    if expected != event["id"]:
        return False
    return PublicKeyXOnly(bytes.fromhex(event["pubkey"])).verify(bytes.fromhex(event["sig"]), bytes.fromhex(event["id"]))


# ---------------------------------------------------------------- the note

def chart_of_the_day(index: dict, day: dt.date) -> dict:
    charts = [c for c in index.get("charts", []) if c.get("title") and c.get("page")]
    if not charts:
        raise SystemExit("charts/index.json has no charts")
    return charts[day.timetuple().tm_yday % len(charts)]


def compose(chart: dict) -> tuple[str, list]:
    page = SITE + chart["page"]
    image = SITE + chart["png"]
    content = f"{chart['title']}.\n\nChart and data: {page}\n\n{image}"
    if len(content) > 300:
        content = f"{chart['title']}.\n{page}\n{image}"
    tags = [["t", "bitcoin"], ["t", "sats"], ["r", page], ["imeta", f"url {image}", "m image/png"]]
    return content, tags


# ---------------------------------------------------------------- publishing

async def _send(relay: str, event: dict, timeout: float) -> str:
    import websockets

    try:
        async with websockets.connect(relay, open_timeout=timeout, close_timeout=5) as ws:
            await ws.send(json.dumps(["EVENT", event]))
            deadline = asyncio.get_event_loop().time() + timeout
            while True:
                remaining = deadline - asyncio.get_event_loop().time()
                if remaining <= 0:
                    return "no OK within timeout"
                raw = await asyncio.wait_for(ws.recv(), timeout=remaining)
                try:
                    msg = json.loads(raw)
                except ValueError:
                    continue
                if isinstance(msg, list) and msg and msg[0] == "OK" and len(msg) >= 3 and msg[1] == event["id"]:
                    return "accepted" if msg[2] else f"rejected: {msg[3] if len(msg) > 3 else ''}"
    except Exception as err:  # noqa: BLE001
        return f"error: {type(err).__name__}: {err}"


async def publish(event: dict, relays: list[str], timeout: float = 15.0) -> dict[str, str]:
    results = await asyncio.gather(*(_send(r, event, timeout) for r in relays))
    return dict(zip(relays, results))


# ---------------------------------------------------------------- self test

def self_test() -> int:
    # BIP-340 test vector 0: secret key 3
    secret = bytes.fromhex("0000000000000000000000000000000000000000000000000000000000000003")
    pub = public_key_hex(secret)
    ok_pub = pub.upper() == "F9308A019258C31049344F85F89D5229B531C845836F99B08601F113BCE036F9"
    print("pubkey from secret 3:", "PASS" if ok_pub else "FAIL " + pub)

    # bech32 round trip and a known npub
    npub = bech32_encode("npub", bytes.fromhex(pub))
    hrp, back = bech32_decode(npub)
    ok_b32 = hrp == "npub" and back.hex() == pub
    print("bech32 round trip:", "PASS" if ok_b32 else "FAIL")
    nsec = bech32_encode("nsec", secret)
    ok_nsec = secret_key_bytes(nsec) == secret and secret_key_bytes(secret.hex()) == secret
    print("nsec decode (bech32 and hex):", "PASS" if ok_nsec else "FAIL")

    # sign and verify an event; tamper and expect failure
    event = sign_event(secret, 1, "test note", [["t", "test"]], created_at=1700000000)
    ok_sig = verify_event(event)
    tampered = dict(event, content="changed")
    ok_tamper = not verify_event(tampered)
    print("event signature verifies:", "PASS" if ok_sig else "FAIL")
    print("tampered event rejected:", "PASS" if ok_tamper else "FAIL")
    # The id must follow NIP-01 serialization exactly
    expected = hashlib.sha256(json.dumps([0, event["pubkey"], 1700000000, 1, [["t", "test"]], "test note"], separators=(",", ":")).encode()).hexdigest()
    ok_id = expected == event["id"]
    print("NIP-01 id:", "PASS" if ok_id else "FAIL")
    return 0 if all([ok_pub, ok_b32, ok_nsec, ok_sig, ok_tamper, ok_id]) else 1


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--relays", default="", help="comma-separated relay URLs (default: the built-in list)")
    parser.add_argument("--index", default=str(INDEX))
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()

    index = json.loads(Path(args.index).read_text(encoding="utf-8"))
    chart = chart_of_the_day(index, dt.date.today())
    content, tags = compose(chart)
    print("Chart of the day:", chart["slug"])
    print("Note:\n" + content + "\n")
    if args.dry_run:
        return 0

    secret_text = os.environ.get("NOSTR_NSEC", "")
    if not secret_text:
        print("NOSTR_NSEC is not set; nothing posted.")
        return 0
    secret = secret_key_bytes(secret_text)
    event = sign_event(secret, 1, content, tags)
    if not verify_event(event):
        print("signature check failed; nothing posted.")
        return 1
    relays = [r.strip() for r in args.relays.split(",") if r.strip()] or RELAYS
    results = asyncio.run(publish(event, relays))
    accepted = 0
    for relay, result in results.items():
        print(f"  {relay}: {result}")
        accepted += result == "accepted"
    print(f"posted as {bech32_encode('npub', bytes.fromhex(event['pubkey']))}, event {event['id']}, accepted by {accepted} of {len(relays)} relays")
    return 0 if accepted else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
