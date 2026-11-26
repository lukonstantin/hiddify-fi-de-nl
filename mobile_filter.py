#!/usr/bin/env python3
"""Refresh mobile-specific subscription; source labels are not reachability tests."""
from subscription_builder import fetch, valid_node, identity
from pathlib import Path

SOURCES = (
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
)

def main():
    nodes = {}
    for source in SOURCES:
        try:
            raw = fetch(source)
            if len(raw) > 5_000_000:
                raise ValueError("Oversized source")
            for line in raw.splitlines():
                line = line.strip()
                if line.startswith("vless://") and valid_node(line):
                    nodes.setdefault(identity(line), line)
        except Exception as exc:
            print("Mobile source failed:", type(exc).__name__)
    if len(nodes) < 5:
        print("Too few mobile candidates; retaining previous subscription")
        return
    output = Path("mobile.txt")
    content = "\n".join(["# profile-title: MOBILE AUTO", "# profile-update-interval: 1", "# Mobile source lists; actual reachability not verified", f"# Count: {len(nodes)}", "", *nodes.values()]) + "\n"
    if not output.exists() or output.read_text(encoding="utf-8") != content:
        temp = output.with_suffix(".tmp")
        temp.write_text(content, encoding="utf-8")
        temp.replace(output)
    print(f"Mobile candidates: {len(nodes)}")

if __name__ == "__main__":
    main()
