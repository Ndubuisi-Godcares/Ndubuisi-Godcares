import os
import requests
from datetime import datetime

TOKEN = os.environ["GH_TOKEN"]
USERNAME = os.environ.get("GH_USERNAME", "Ndubuisi-Godcares")

HEADERS = {
    "Authorization": f"bearer {TOKEN}",
    "Content-Type": "application/json"
}

YEARS_QUERY = """
query($username: String!) {
  user(login: $username) {
    contributionsCollection {
      contributionYears
    }
  }
}
"""

YEAR_QUERY = """
query($username: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $username) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
    }
  }
}
"""

def gql(query, variables):
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": variables},
        headers=HEADERS
    )
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise Exception(data["errors"])
    return data["data"]

def fetch_all_stats():
    data = gql(YEARS_QUERY, {"username": USERNAME})
    years = data["user"]["contributionsCollection"]["contributionYears"]

    totals = {"commits": 0, "issues": 0, "prs": 0, "reviews": 0}

    for year in years:
        from_dt = f"{year}-01-01T00:00:00Z"
        to_dt   = f"{year}-12-31T23:59:59Z"
        y = gql(YEAR_QUERY, {"username": USERNAME, "from": from_dt, "to": to_dt})
        c = y["user"]["contributionsCollection"]
        totals["commits"]  += c["totalCommitContributions"]
        totals["issues"]   += c["totalIssueContributions"]
        totals["prs"]      += c["totalPullRequestContributions"]
        totals["reviews"]  += c["totalPullRequestReviewContributions"]
        print(f"  {year}: commits={c['totalCommitContributions']} issues={c['totalIssueContributions']} prs={c['totalPullRequestContributions']} reviews={c['totalPullRequestReviewContributions']}")

    print(f"All-time totals: {totals}")
    return totals

def format_pct(pct):
    rounded = round(pct * 100)
    if pct > 0 and rounded == 0:
        return "<1%"
    return f"{rounded}%"

def make_radar_svg(stats):
    total = sum(stats.values()) or 1
    commits_pct = stats["commits"] / total
    issues_pct  = stats["issues"]  / total
    prs_pct     = stats["prs"]     / total
    reviews_pct = stats["reviews"] / total

    cx, cy, r_max = 220, 185, 110

    axes = [
        (cx,           cy - r_max, reviews_pct, format_pct(reviews_pct), "Code review",  "middle",  0,  -18),
        (cx + r_max,   cy,         issues_pct,  format_pct(issues_pct),  "Issues",       "start",   14,   0),
        (cx,           cy + r_max, prs_pct,     format_pct(prs_pct),     "Pull requests","middle",  0,   20),
        (cx - r_max,   cy,         commits_pct, format_pct(commits_pct), "Commits",      "end",    -14,   0),
    ]

    pts = []
    for ax, ay, pct, *_ in axes:
        effective = max(pct, 0.03) if pct > 0 else 0
        dx, dy = ax - cx, ay - cy
        pts.append((cx + dx * effective, cy + dy * effective))

    polygon = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)

    dot_els = ""
    for x, y in pts:
        dot_els += f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="#39d353"/>\n    '

    label_els = ""
    for ax, ay, pct, pct_label, name, anchor, ldx, ldy in axes:
        lx, ly = ax + ldx, ay + ldy
        pct_dy = -14 if ldy <= 0 else 14
        label_els += (
            f'<text x="{lx}" y="{ly + pct_dy}" text-anchor="{anchor}" '
            f'font-family="monospace" font-size="13" fill="#e6edf3" font-weight="500">'
            f'{pct_label}</text>\n    '
            f'<text x="{lx}" y="{ly + pct_dy + 16}" text-anchor="{anchor}" '
            f'font-family="monospace" font-size="11" fill="#8b949e">{name}</text>\n    '
        )

    rings = ""
    for i in [0.25, 0.5, 0.75, 1.0]:
        rings += f'<circle cx="{cx}" cy="{cy}" r="{r_max*i:.1f}" fill="none" stroke="#21262d" stroke-width="0.5"/>\n  '

    updated = datetime.utcnow().strftime("%Y-%m-%d")

    svg = f"""<svg width="440" height="370" viewBox="0 0 440 370" xmlns="http://www.w3.org/2000/svg">
  <rect width="440" height="370" rx="10" fill="#0d1117"/>
  {rings}
  <line x1="{cx}" y1="{cy - r_max}" x2="{cx}" y2="{cy + r_max}" stroke="#21262d" stroke-width="1"/>
  <line x1="{cx - r_max}" y1="{cy}" x2="{cx + r_max}" y2="{cy}" stroke="#21262d" stroke-width="1"/>
  <polygon points="{polygon}" fill="rgba(57,211,83,0.2)" stroke="#39d353" stroke-width="1.5"/>
  {dot_els}
  {label_els}
  <text x="{cx}" y="355" text-anchor="middle" font-family="monospace" font-size="10" fill="#484f58">updated {updated} · all-time contributions</text>
</svg>"""
    return svg

def main():
    print(f"Fetching all-time stats for {USERNAME}...")
    stats = fetch_all_stats()
    svg = make_radar_svg(stats)
    os.makedirs("assets", exist_ok=True)
    with open("assets/activity-radar.svg", "w") as f:
        f.write(svg)
    print("Generated assets/activity-radar.svg")

if __name__ == "__main__":
    main()
