#!/usr/bin/env python3

import base64
import json
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

OUTPUT = "europe.txt"

# Основной источник: часто обновляемый список уже проверенных endpoint'ов.
PRIMARY_SOURCE = (
    "https://raw.githubusercontent.com/"
    "aviamastersgh/vpn-free-russia/main/verified_configs.txt"
)

# Эти источники используются для добора, если в основном списке
# оказалось мало европейских серверов.
BACKUP_SOURCES = (
    "https://raw.githubusercontent.com/"
    "igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt",

    "https://raw.githubusercontent.com/"
    "igareck/vpn-configs-for-russia/main/BLACK_SS%2BAll_RUS.txt",
)

COUNTRY_NAMES = (
    "finland",
    "germany",
    "netherlands",
    "poland",
    "sweden",
    "france",
    "switzerland",
    "austria",
    "czechia",
    "czech republic",
    "estonia",
    "latvia",
    "lithuania",
    "belgium",
    "denmark",
    "norway",
    "united kingdom",
    "great britain",
    "ireland",
)

COUNTRY_FLAGS = (
    "🇫🇮",
    "🇩🇪",
    "🇳🇱",
    "🇵🇱",
    "🇸🇪",
    "🇫🇷",
    "🇨🇭",
    "🇦🇹",
    "🇨🇿",
    "🇪🇪",
    "🇱🇻",
    "🇱🇹",
    "🇧🇪",
    "🇩🇰",
    "🇳🇴",
    "🇬🇧",
    "🇮🇪",
)

ALLOWED_SCHEMES = (
    "vless",
    "trojan",
    "vmess",
    "ss",
    "hysteria2",
    "hy2",
    "tuic",
)

# Если основной проверенный список дал хотя бы столько нод,
# дополнительные источники не нужны.
TARGET_COUNT = 30

# Если внезапно даже 5 нод собрать не удалось —
# старый europe.txt лучше сохранить.
MIN_COUNT = 5


def fetch(url: str) -> str:
    req = Request(
        url,
        headers={"User-Agent": "hiddify-europe-auto/2.0"}
    )

    with urlopen(req, timeout=30) as response:
        return response.read().decode(
            "utf-8",
            errors="replace"
        )


def decode_vmess(line: str):
    payload = line[len("vmess://"):].split("#", 1)[0]
    payload += "=" * (-len(payload) % 4)

    try:
        decoded = base64.urlsafe_b64decode(
            payload.encode("ascii")
        ).decode("utf-8")

        return json.loads(decoded)

    except Exception:
        return {}


def get_label(line: str) -> str:
    if line.startswith("vmess://"):
        data = decode_vmess(line)
        return str(data.get("ps", ""))

    if "#" in line:
        return unquote(
            line.split("#", 1)[1],
            errors="replace"
        )

    return ""


def is_europe(line: str) -> bool:
    label = get_label(line)
    low = label.lower()

    # Anycast может иметь одновременно европейский и азиатский флаг.
    # Такие конфиги нам не нужны.
    if "anycast" in low:
        return False

    return (
        any(country in low for country in COUNTRY_NAMES)
        or any(flag in label for flag in COUNTRY_FLAGS)
    )


def get_scheme(line: str) -> str:
    if "://" not in line:
        return ""

    return line.split("://", 1)[0].lower()


def endpoint_key(line: str) -> str:
    """
    Убираем десяток почти одинаковых записей одного сервера.
    Ключ: протокол + сервер + порт.
    """

    scheme = get_scheme(line)

    if scheme == "vmess":
        data = decode_vmess(line)

        host = str(data.get("add", "")).lower().strip()
        port = str(data.get("port", "")).strip()

        if host and port:
            return f"{scheme}|{host}|{port}"

        return line

    try:
        parsed = urlsplit(line)

        host = parsed.hostname
        port = parsed.port

        if host and port:
            return (
                f"{scheme}|"
                f"{host.lower()}|"
                f"{port}"
            )

    except Exception:
        pass

    return line


def add_nodes(text: str, nodes: list, seen: set):
    for raw in text.splitlines():
        line = raw.strip()

        if not line or line.startswith("#"):
            continue

        scheme = get_scheme(line)

        if scheme not in ALLOWED_SCHEMES:
            continue

        if not is_europe(line):
            continue

        key = endpoint_key(line)

        if key in seen:
            continue

        seen.add(key)
        nodes.append(line)


nodes = []
seen = set()


# 1. Сначала берём свежие проверенные серверы.
try:
    primary_text = fetch(PRIMARY_SOURCE)
    add_nodes(primary_text, nodes, seen)

except Exception as exc:
    print(f"Primary source failed: {exc}")


primary_count = len(nodes)

print(
    f"Verified European nodes: {primary_count}"
)


# 2. Старые источники используются только как резерв.
if len(nodes) < TARGET_COUNT:

    for source in BACKUP_SOURCES:

        try:
            text = fetch(source)
            add_nodes(text, nodes, seen)

        except Exception as exc:
            print(
                f"Backup source failed: {exc}"
            )


if len(nodes) < MIN_COUNT:
    print(
        f"Only {len(nodes)} European nodes found; "
        "keeping existing europe.txt"
    )

    raise SystemExit(0)


header = [
    "# profile-title: 🇪🇺 EUROPE AUTO",
    "# profile-update-interval: 1",
    "# Primary: aviamastersgh verified_configs",
    "# Backup: igareck verified Russia lists",
    "# Deduplicated by protocol/server/port",
    "# Countries: Europe only",
    f"# Verified primary: {primary_count}",
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