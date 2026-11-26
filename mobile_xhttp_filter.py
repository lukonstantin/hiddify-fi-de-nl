from pathlib import Path
from urllib.parse import urlsplit, parse_qs

def main():
    nodes = []
    for line in Path("mobile.txt").read_text(encoding="utf-8").splitlines():
        if not line.startswith("vless://"):
            continue
        try:
            q = parse_qs(urlsplit(line).query)
        except ValueError:
            continue
        if q.get("type") == ["xhttp"] and q.get("security") == ["reality"]:
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
