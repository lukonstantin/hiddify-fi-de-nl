#!/usr/bin/env python3
"""Build Hiddify-compatible subscriptions from multiple public feeds.

Country classification is based on provider labels, not verified geolocation.
"""
import base64
import json
import os
import re
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

SOURCES = (
    "https://raw.githubusercontent.com/aviamastersgh/vpn-free-russia/main/verified_configs.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_SS%2BAll_RUS.txt",
)
COUNTRIES = {
    "finland": "🇫🇮", "germany": "🇩🇪", "netherlands": "🇳🇱",
    "poland": "🇵🇱", "sweden": "🇸🇪", "france": "🇫🇷",
    "switzerland": "🇨🇭", "austria": "🇦🇹", "czechia": "🇨🇿",
    "czech republic": "🇨🇿", "estonia": "🇪🇪", "latvia": "🇱🇻",
    "lithuania": "🇱🇹", "belgium": "🇧🇪", "denmark": "🇩🇰",
    "norway": "🇳🇴", "united kingdom": "🇬🇧", "great britain": "🇬🇧",
    "ireland": "🇮🇪",
}
SCHEMES = {"vless", "trojan", "vmess", "ss", "hysteria2", "hy2", "tuic"}
MIN_COUNT = 5


def decode_vmess(line):
    try:
        payload = line[8:].split("#", 1)[0]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.b64decode(payload, altchars=b"-_", validate=True).decode("utf-8"))
    except (ValueError, UnicodeError, TypeError):
        return {}


def label_of(line):
    if line.lower().startswith("vmess://"):
        return str(decode_vmess(line).get("ps", ""))
    return unquote(line.split("#", 1)[1]) if "#" in line else ""


def valid_node(line):
    if "://" not in line or any(c.isspace() for c in line.split("#", 1)[0]):
        return False
    scheme = line.split("://", 1)[0].lower()
    if scheme not in SCHEMES:
        return False
    if scheme == "vmess":
        data = decode_vmess(line)
        return bool(data.get("add") and str(data.get("port", "")).isdigit())
    try:
        parsed = urlsplit(line)
        return bool(parsed.hostname and parsed.port and parsed.username)
    except ValueError:
        return False


def matches_country(line, allowed):
    label = label_of(line)
    low = label.casefold()
    if "anycast" in low:
        return False
    for country, flag in COUNTRIES.items():
        if country in allowed and (flag in label or re.search(r"(?<![a-z])" + re.escape(country) + r"(?![a-z])", low)):
            return True
    return False


def identity(line):
    # Preserve distinct credentials, transport settings, SNI and paths.
    # Only remove the display label from URI configs.
    if line.lower().startswith("vmess://"):
        data = decode_vmess(line)
        data.pop("ps", None)
        return "vmess:" + json.dumps(data, sort_keys=True, ensure_ascii=False)
    return line.split("#", 1)[0]


def fetch(source):
    req = Request(source, headers={"User-Agent": "hiddify-subscription-builder/3.0"})
    with urlopen(req, timeout=20) as response:
        return response.read(5_000_001).decode("utf-8", errors="replace")


def build(output, title, allowed, minimum=MIN_COUNT):
    nodes, seen = [], set()
    for source in SOURCES:
        try:
            raw = fetch(source)
            if len(raw) > 5_000_000:
                raise ValueError("Source exceeds 5 MB")
            added = 0
            for line in raw.splitlines():
                line = line.strip()
                if not valid_node(line) or not matches_country(line, allowed):
                    continue
                key = identity(line)
                if key in seen:
                    continue
                seen.add(key)
                nodes.append(line)
                added += 1
            print(f"{source}: +{added} nodes")
        except Exception as exc:
            print(f"Source failed ({source}): {exc}")

    if len(nodes) < minimum:
        print(f"Only {len(nodes)} nodes; keeping existing {output}")
        return False

    header = [
        f"# profile-title: {title}",
        "# profile-update-interval: 1",
        "# Countries inferred from source labels; reachability NOT tested",
        f"# Count: {len(nodes)}",
        "",
    ]
    content = "\n".join(header + nodes) + "\n"
    # Avoid unnecessary commits when the source list is unchanged.
    if os.path.exists(output):
        with open(output, encoding="utf-8") as file:
            if file.read() == content:
                print(f"No change: {output}")
                return True
    temp = output + ".tmp"
    with open(temp, "w", encoding="utf-8", newline="\n") as file:
        file.write(content)
    os.replace(temp, output)
    print(f"Wrote {len(nodes)} nodes to {output}")
    return True
