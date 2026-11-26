from pathlib import Path
from subscription_builder import fetch, valid_node
from urllib.parse import urlsplit, parse_qs

def main():
    nodes = []
    seen = set()
    raw = Path("mobile.txt").read_text(encoding="utf-8")
    for source in (
        'https://raw.githubusercontent.com/aviamastersgh/vpn-free-russia/main/verified_configs.txt',
        'https://raw.githubusercontent.com/pie-with-jam/PulseProxy/main/githubmirror/30.txt',
    ):
        try:
            raw += '\n' + fetch(source)
        except Exception as exc:
            print('Additional source unavailable:', type(exc).__name__)
    for line in raw.splitlines():
        line = line.strip()
        if not line.startswith("vless://") or not valid_node(line):
            continue
        try:
            q = parse_qs(urlsplit(line).query)
        except ValueError:
            continue
        if q.get("type") == ["xhttp"] and q.get("security") == ["reality"]:
            key = line.split('#', 1)[0]
            if key not in seen:
                seen.add(key)
                nodes.append(line)
    if not nodes:
        print("No matching candidates; keeping previous list")
        return
    output = Path("mobile-xhttp.txt")
    temp = output.with_suffix(".tmp")
    temp.write_text("\n".join(["# profile-title: MOBILE XHTTP", "# profile-update-interval: 1", "# Reachability not verified", f"# Count: {len(nodes)}", "", *nodes, ""]), encoding="utf-8")
    temp.replace(output)
    print(f"XHTTP candidates: {len(nodes)}")

if __name__ == "__main__":
    main()
