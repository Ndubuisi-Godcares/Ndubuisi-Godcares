import os
import math
import requests

TOKEN = os.environ["GH_TOKEN"]
USERNAME = os.environ.get("GH_USERNAME", "Ndubuisi-Godcares")

HEADERS = {
    "Authorization": f"bearer {TOKEN}",
    "Content-Type": "application/json"
}

QUERY = """
query($username: String!) {
  user(login: $username) {
    contributionsCollection {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
    }
  }
}
"""

def fetch_stats():
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": QUERY, "variables": {"username": USERNAME}},
        headers=HEADERS
    )
    r.raise_for_status()
    data = r.json()
    c = data["data"]["user"]["contributionsCollection"]
    return {
        "commits": c["totalCommitContributions"],
        "issues": c["totalIssueContributions"],
        "prs": c["totalPullRequestContributions"],
        "reviews": c["totalPullRequestReviewContributions"],
    }

def make_radar_svg(stats):
    total = sum(stats.values()) or 1
    commits_pct  = stats["commits"]  / total
    issues_pct   = stats["issues"]   / total
    prs_pct      = stats["prs"]      / total
    reviews_pct  = stats["reviews"]  / total

    cx, cy, r_max = 220, 175, 110

    # axes: top=reviews, right=issues, bottom=prs, left=commits
    axes = [
        (cx,            cy - r_max,  reviews_pct,  f"{round(reviews_pct*100)}%", "Code review", "middle", 0, -18),
        (cx + r_max,    cy,          issues_pct,   f"{round(issues_pct*100)}%",  "Issues",      "start",  14,  0),
        (cx,            cy + r_max,  prs_pct,      f"{round(prs_pct*100)}%",     "Pull requests","middle", 0,  20),
        (cx - r_max,    cy,          commits_pct,  f"{round(commits_pct*100)}%", "Commits",     "end",   -14,  0),
    ]

    pts = []
    for ax, ay, pct, *_ in axes:
        dx, dy = ax - cx, ay - cy
        pts.append((cx + dx * pct, cy + dy * pct))

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

    svg = f"""<svg width="440" height="350" viewBox="0 0 440 350" xmlns="http://www.w3.org/2000/svg">
  <rect width="440" height="350" rx="10" fill="#0d1117"/>

  <!-- grid rings -->
  <circle cx="{cx}" cy="{cy}" r="{r_max*0.25:.1f}" fill="none" stroke="#21262d" stroke-width="0.5"/>
  <circle cx="{cx}" cy="{cy}" r="{r_max*0.5:.1f}"  fill="none" stroke="#21262d" stroke-width="0.5"/>
  <circle cx="{cx}" cy="{cy}" r="{r_max*0.75:.1f}" fill="none" stroke="#21262d" stroke-width="0.5"/>
  <circle cx="{cx}" cy="{cy}" r="{r_max:.1f}"      fill="none" stroke="#21262d" stroke-width="0.5"/>

  <!-- axes -->
  <line x1="{cx}" y1="{cy - r_max}" x2="{cx}" y2="{cy + r_max}" stroke="#21262d" stroke-width="1"/>
  <line x1="{cx - r_max}" y1="{cy}" x2="{cx + r_max}" y2="{cy}" stroke="#21262d" stroke-width="1"/>

  <!-- radar fill -->
  <polygon points="{polygon}" fill="rgba(57,211,83,0.2)" stroke="#39d353" stroke-width="1.5"/>

  <!-- dots -->
  {dot_els}

  <!-- labels -->
  {label_els}
</svg>"""
    return svg

def main():
    stats = fetch_stats()
    svg = make_radar_svg(stats)
    os.makedirs("assets", exist_ok=True)
    with open("assets/activity-radar.svg", "w") as f:
        f.write(svg)
    print("Generated assets/activity-radar.svg")
    print(stats)

if __name__ == "__main__":
    main()
