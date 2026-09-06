#!/usr/bin/env python3

import base64
import json
from urllib.parse import unquote
from urllib.request import Request, urlopen

SOURCE = "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_SS%2BAll_RUS.txt"
OUTPUT = "filtered.txt"

COUNTRY_NAMES = ("finland", "germany", "netherlands")
COUNTRY_FLAGS = ("🇫🇮", "🇩🇪", "🇳🇱")


def get_label(line: str) -> str:
    if line.startswith("vmess://"):
        payload = line[len("vmess://"):].split("#", 1)[0]
        payload += "=" * (-len(payload) % 4)

        try:
            decoded = base64.urlsafe_b64decode(
                payload.encode("ascii")
            ).decode("utf-8")

            data = json.loads(decoded)
            return str(data.get("ps", ""))

        except Exception:
            return ""

    if "#" in line:
        return unquote(
            line.split("#", 1)[1],
            errors="replace"
        )

    return unquote(line, errors="replace")


def wanted(line: str) -> bool:
    label = get_label(line)
    low = label.lower()

    return (
        any(country in low for country in COUNTRY_NAMES)
        or any(flag in label for flag in COUNTRY_FLAGS)
    )


req = Request(
    SOURCE,
    headers={
        "User-Agent": "hiddify-fi-de-nl-filter/1.0"
    }
)

with urlopen(req, timeout=30) as response:
    source_text = response.read().decode(
        "utf-8",
        errors="replace"
    )


nodes = []
seen = set()

for raw in source_text.splitlines():
    line = raw.strip()

    if not line or line.startswith("#"):
        continue

    if wanted(line) and line not in seen:
        seen.add(line)
        nodes.append(line)


if not nodes:
    raise SystemExit(
        "No FI/DE/NL nodes found; refusing to overwrite filtered.txt"
    )


header = [
    "# profile-title: 🇫🇮🇩🇪🇳🇱 FI-DE-NL AUTO",
    "# profile-update-interval: 1",
    "# Auto-filtered from igareck/vpn-configs-for-russia",
    "# Countries: Finland, Germany, Netherlands",
    f"# Count: {len(nodes)}",
    "",
]


with open(
    OUTPUT,
    "w",
    encoding="utf-8",
    newline="\n"
) as f:

    f.write(
        "\n".join(header + nodes) + "\n"
    )


print(
    f"Wrote {len(nodes)} nodes to {OUTPUT}"
)
