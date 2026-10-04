"""Renders assets/activity-graph.svg: last 31 days of contributions as a line chart.

Runs in GitHub Actions (see .github/workflows/activity-graph.yml) with GITHUB_TOKEN.
Local preview with fake data:  python3 assets/render_graph.py --demo
"""
import datetime as dt
import json
import os
import random
import sys
import urllib.request
from pathlib import Path

USER = os.environ.get("GH_USER", "TacoGod900")
TITLE = os.environ.get("GRAPH_TITLE", "Henryk's Contribution Graph")
OUT = Path(__file__).parent / "activity-graph.svg"
DAYS = 31

# github-compact look
BG, GRID, LINE, AREA, POINT, TEXT, MUTED = (
    "#0d1117", "#30363d", "#58a6ff", "#58a6ff", "#ffffff", "#e6edf3", "#8b949e")
W, H = 1200, 420
L, R, T, B = 70, 30, 70, 70  # plot margins


def fetch_days():
    today = dt.date.today()
    start = today - dt.timedelta(days=DAYS - 1)
    query = """
    query($u:String!, $from:DateTime!, $to:DateTime!) {
      user(login:$u) { contributionsCollection(from:$from, to:$to) {
        contributionCalendar { weeks { contributionDays { date contributionCount } } } } } }"""
    body = json.dumps({"query": query, "variables": {
        "u": USER, "from": f"{start}T00:00:00Z", "to": f"{today}T23:59:59Z"}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",
                 "Content-Type": "application/json", "User-Agent": USER})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(f"GraphQL error: {data['errors']}")
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    counts = {d["date"]: d["contributionCount"] for w in weeks for d in w["contributionDays"]}
    days = [start + dt.timedelta(days=i) for i in range(DAYS)]
    return [(d, counts.get(d.isoformat(), 0)) for d in days]


def demo_days():
    random.seed(7)
    today = dt.date.today()
    return [(today - dt.timedelta(days=DAYS - 1 - i), random.choice([0, 2, 5, 9, 14, 22, 31]))
            for i in range(DAYS)]


def render(days):
    pw, ph = W - L - R, H - T - B
    ymax = max(5, max(c for _, c in days))
    # round the axis top up to a tidy number
    step = 5 if ymax <= 25 else 10 if ymax <= 60 else 25 if ymax <= 150 else 50
    ymax = ((ymax + step - 1) // step) * step
    xs = [L + pw * i / (DAYS - 1) for i in range(DAYS)]
    ys = [T + ph - ph * c / ymax for _, c in days]

    # smooth-ish path with Catmull-Rom -> cubic bezier
    pts = list(zip(xs, ys))
    def path():
        d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        for i in range(len(pts) - 1):
            p0 = pts[i - 1] if i else pts[i]
            p1, p2 = pts[i], pts[i + 1]
            p3 = pts[i + 2] if i + 2 < len(pts) else p2
            lo, hi = T, T + ph  # keep the curve inside the plot (no dips below zero)
            c1 = (p1[0] + (p2[0] - p0[0]) / 6, min(hi, max(lo, p1[1] + (p2[1] - p0[1]) / 6)))
            c2 = (p2[0] - (p3[0] - p1[0]) / 6, min(hi, max(lo, p2[1] - (p3[1] - p1[1]) / 6)))
            d += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
        return d
    line = path()
    area = f"{line} L{xs[-1]:.1f},{T + ph} L{xs[0]:.1f},{T + ph} Z"

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="Segoe UI, Ubuntu, Helvetica, Arial, sans-serif">',
         f'<rect width="{W}" height="{H}" rx="6" fill="{BG}"/>',
         f'<text x="{W/2}" y="38" text-anchor="middle" fill="{TEXT}" font-size="18" font-weight="600">{TITLE}</text>']
    # horizontal grid + y labels
    for i in range(0, ymax + 1, step):
        y = T + ph - ph * i / ymax
        s.append(f'<line x1="{L}" y1="{y:.1f}" x2="{L + pw}" y2="{y:.1f}" stroke="{GRID}" stroke-dasharray="4 4"/>')
        s.append(f'<text x="{L - 12}" y="{y + 4:.1f}" text-anchor="end" fill="{MUTED}" font-size="11">{i}</text>')
    # x labels (every other day)
    for i, (d, _) in enumerate(days):
        if i % 2 == 0 or i == DAYS - 1:
            s.append(f'<text x="{xs[i]:.1f}" y="{T + ph + 22}" text-anchor="middle" fill="{MUTED}" font-size="11">{d.day}</text>')
    s.append(f'<text x="{L + pw/2}" y="{H - 18}" text-anchor="middle" fill="{MUTED}" font-size="12">Days</text>')
    s.append(f'<path d="{area}" fill="{AREA}" fill-opacity="0.12"/>')
    s.append(f'<path d="{line}" fill="none" stroke="{LINE}" stroke-width="2.5" stroke-linejoin="round"/>')
    for (x, y), (d, c) in zip(pts, days):
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{POINT}"><title>{d}: {c} contributions</title></circle>')
    s.append('</svg>')
    return "\n".join(s)


if __name__ == "__main__":
    days = demo_days() if "--demo" in sys.argv else fetch_days()
    OUT.write_text(render(days))
    print(f"wrote {OUT} ({sum(c for _, c in days)} contributions over {DAYS} days)")
