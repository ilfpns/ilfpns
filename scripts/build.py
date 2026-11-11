"""Generate the light/dark SVG cards used by README.md.

Static cards (header, projects) come from the data below.
Stats cards (activity, languages) are pulled from the GitHub GraphQL API
using GITHUB_TOKEN, so the workflow can refresh them daily.
"""
import json
import os
import urllib.request
from datetime import datetime, timezone
from html import escape
from pathlib import Path

USER = "ilfpns"
# markup, build scripts and notebook output distort byte counts
IGNORED_LANGS = {"Jupyter Notebook", "HTML", "CSS", "Batchfile", "PowerShell", "Shell", "Makefile", "CMake"}
OUT = Path(__file__).resolve().parent.parent / "assets"

FONT = ("text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Apple SD Gothic Neo',"
        "'Malgun Gothic','Noto Sans KR','Noto Sans',Helvetica,Arial,sans-serif}")

THEMES = {
    "dark": dict(bg="#0d1117", border="#30363d", fg="#e6edf3", muted="#9198a1", accent="#4493f8", track="#21262d"),
    "light": dict(bg="#ffffff", border="#d1d9e0", fg="#1f2328", muted="#59636e", accent="#0969da", track="#eff2f5"),
}

HEADER = dict(
    name="Sehyeon Yeom",
    sub="염세현  ·  AI & Embedded Engineer  ·  Daedeok Software Meister High School",
)

STACK = [
    ("Language", "C  ·  C++  ·  Python"),
    ("MCU · Board", "STM32  ·  ESP32  ·  Raspberry Pi  ·  Zynq-7000  ·  Jetson"),
    ("RTOS · Embedded Linux", "Bare-metal  ·  FreeRTOS  ·  Linux  ·  PetaLinux  ·  U-Boot"),
    ("Protocol", "UART  ·  SPI  ·  I2C  ·  MQTT  ·  BLE"),
    ("AI", "PyTorch  ·  TFLite Micro  ·  OpenCV  ·  GStreamer"),
    ("Tools", "Git  ·  Notion  ·  Obsidian  ·  QEMU  ·  Linear"),
]

PROJECTS = [
    dict(slug="phosem", title="PhoSem", desc="PIN 다이오드 불량 검출 AI", tags="Python  ·  PyTorch"),
    dict(slug="pith", title="pith", desc="STM32 베어메탈 RTOS", tags="C  ·  STM32"),
    dict(slug="quant", title="Quant", desc="PyTorch 모델 양자화 실험", tags="Python  ·  TensorRT"),
]


def svg(w, h, label, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(label)}"><style>{FONT}</style>{body}</svg>')


def frame(w, h, t):
    return f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="6" fill="{t["bg"]}" stroke="{t["border"]}"/>'


def header(t):
    body = (f'<text x="0" y="52" font-size="38" font-weight="700" letter-spacing="-1" fill="{t["fg"]}">{escape(HEADER["name"])}</text>'
            f'<text x="2" y="86" font-size="16" fill="{t["muted"]}">{escape(HEADER["sub"])}</text>'
            f'<rect x="2" y="104" width="40" height="3" rx="1.5" fill="{t["accent"]}"/>')
    return svg(708, 120, f'{HEADER["name"]}, AI & Embedded Engineer', body)


def project(p, t):
    w, h = 230, 104
    body = frame(w, h, t)
    body += f'<text x="18" y="32" font-size="15" font-weight="600" fill="{t["accent"]}">{escape(p["title"])}</text>'
    body += f'<text x="18" y="58" font-size="13" fill="{t["fg"]}">{escape(p["desc"])}</text>'
    body += f'<text x="18" y="86" font-size="12" fill="{t["muted"]}">{escape(p["tags"])}</text>'
    return svg(w, h, p["title"], body)


def stack_card(t):
    w, h = 708, 70 + len(STACK) * 30
    body = frame(w, h, t) + section_title("Tech Stack", t)
    for i, (label, items) in enumerate(STACK):
        y = 72 + i * 30
        if i:
            body += f'<line x1="24" y1="{y - 19}" x2="{w - 24}" y2="{y - 19}" stroke="{t["border"]}" stroke-width="1"/>'
        body += (f'<text x="24" y="{y}" font-size="13" fill="{t["muted"]}">{escape(label)}</text>'
                 f'<text x="210" y="{y}" font-size="13" fill="{t["fg"]}">{escape(items)}</text>')
    return svg(w, h, "Tech Stack", body)


def section_title(title, t):
    return (f'<rect x="24" y="24" width="3" height="16" rx="1.5" fill="{t["accent"]}"/>'
            f'<text x="35" y="37" font-size="15" font-weight="600" fill="{t["fg"]}">{escape(title)}</text>')


def stats_card(rows, t):
    body = frame(350, 200, t) + section_title("Activity", t)
    for i, (k, v) in enumerate(rows):
        y = 70 + i * 26
        body += (f'<text x="24" y="{y}" font-size="13" fill="{t["muted"]}">{escape(k)}</text>'
                 f'<text x="326" y="{y}" font-size="13" font-weight="600" fill="{t["fg"]}" text-anchor="end">{v:,}</text>')
    return svg(350, 200, "Activity", body)


def langs_card(langs, t):
    body = frame(350, 200, t) + section_title("Most Used Languages", t)
    total = sum(b for _, b, _ in langs) or 1
    # stacked bar
    x, bar_w = 24.0, 302
    body += f'<clipPath id="c"><rect x="24" y="56" width="{bar_w}" height="8" rx="4"/></clipPath><g clip-path="url(#c)">'
    body += f'<rect x="24" y="56" width="{bar_w}" height="8" fill="{t["track"]}"/>'
    for _, b, color in langs:
        w = bar_w * b / total
        body += f'<rect x="{x:.2f}" y="56" width="{w:.2f}" height="8" fill="{color}"/>'
        x += w
    body += '</g>'
    for i, (name, b, color) in enumerate(langs):
        col, row = i % 2, i // 2
        cx, cy = 24 + col * 156, 96 + row * 26
        body += (f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{color}"/>'
                 f'<text x="{cx + 16}" y="{cy}" font-size="13" fill="{t["fg"]}">{escape(name)}</text>'
                 f'<text x="{cx + 140}" y="{cy}" font-size="13" fill="{t["muted"]}" text-anchor="end">{b / total * 100:.1f}%</text>')
    return svg(350, 200, "Most Used Languages", body)


def graphql(query, variables):
    token = os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def fetch_stats():
    year = datetime.now(timezone.utc).year
    q = """query($login:String!,$from:DateTime!){user(login:$login){
      contributionsCollection(from:$from){contributionCalendar{totalContributions} totalCommitContributions totalRepositoriesWithContributedCommits}
      pullRequests{totalCount}
      repositories(ownerAffiliations:OWNER,isFork:false,first:100,privacy:PUBLIC){
        totalCount
        nodes{languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}}}"""
    u = graphql(q, {"login": USER, "from": f"{year}-01-01T00:00:00Z"})["user"]
    cc = u["contributionsCollection"]
    repos = u["repositories"]["nodes"]
    rows = [
        (f"Contributions ({year})", cc["contributionCalendar"]["totalContributions"]),
        (f"Commits ({year})", cc["totalCommitContributions"]),
        ("Public repositories", u["repositories"]["totalCount"]),
        ("Pull requests", u["pullRequests"]["totalCount"]),
        (f"Repos committed to ({year})", cc["totalRepositoriesWithContributedCommits"]),
    ]
    sizes = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            n = e["node"]
            if n["name"] in IGNORED_LANGS:
                continue
            name, color = n["name"], n["color"] or "#8b949e"
            sizes[name] = (sizes.get(name, (0, color))[0] + e["size"], color)
    top = sorted(sizes.items(), key=lambda kv: -kv[1][0])[:6]
    langs = [(name, size, color) for name, (size, color) in top]
    return rows, langs


def write(name, content):
    (OUT / name).write_text(content + "\n", encoding="utf-8")


def main():
    OUT.mkdir(exist_ok=True)
    rows, langs = fetch_stats()
    for mode, t in THEMES.items():
        write(f"header-{mode}.svg", header(t))
        write(f"stack-{mode}.svg", stack_card(t))
        for p in PROJECTS:
            write(f"card-{p['slug']}-{mode}.svg", project(p, t))
        write(f"stats-{mode}.svg", stats_card(rows, t))
        write(f"langs-{mode}.svg", langs_card(langs, t))


if __name__ == "__main__":
    main()
