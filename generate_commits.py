import requests
from datetime import datetime, timedelta, timezone
import os
import html

# ---------------- CONFIG ----------------

REPOSITORIES = [
    "openedx/edx-platform",
    "openedx/frontend-app-learning",
    "openedx/frontend-app-authoring",
    "openedx/frontend-app-discussions",
]

# GitHub token from environment (set in GitHub Actions)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# ----------------------------------------

headers = {}
if GITHUB_TOKEN:
    headers["Authorization"] = f"token {GITHUB_TOKEN}"

since_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

all_commits = []

for repo in REPOSITORIES:
    url = f"https://api.github.com/repos/{repo}/commits"
    params = {"since": since_time}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    for commit in response.json():
        all_commits.append({
            "repo": repo,
            "message": commit["commit"]["message"].split("\n")[0],
            "author": commit["commit"]["author"]["name"],
            "date": commit["commit"]["author"]["date"],
            "url": commit["html_url"],
        })

all_commits.sort(key=lambda c: c["date"], reverse=True)

# ----------- HTML OUTPUT --------------

html_output = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Open Source Daily Commits Dashboard</title>

<!-- GitHub Primer CSS -->
<link rel="stylesheet" href="https://unpkg.com/@primer/css/dist/primer.css">

<meta name="viewport" content="width=device-width, initial-scale=1">

<style>
.container-lg {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}
.commit-card {
  border: 1px solid #d0d7de;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 12px;
  background: #ffffff;
}
.repo-badge {
  font-weight: 600;
  color: #0969da;
}
.commit-message {
  font-size: 16px;
  margin: 6px 0;
}
.meta {
  font-size: 13px;
  color: #57606a;
}
.footer-note {
  margin-top: 30px;
  color: #57606a;
  font-size: 12px;
}
</style>
</head>

<body class="color-bg-subtle">

<div class="container-lg">

<h1 class="h1">🚀 Open Source Commits (last 24 hours)</h1>
<p class="color-fg-muted">Automatically generated via GitHub Actions & GitHub Pages</p>

<hr>
"""


for c in all_commits:
    html_output += f"""
    <div class="commit-card">
        <div class="repo-badge">{html.escape(c['repo'])}</div>
        <div class="commit-message">{html.escape(c['message'])}</div>
        <div class="meta">
            👤 {html.escape(c['author'])}<br>
            🕒 {html.escape(c['date'])}<br>
            🔗 <a href="{c['url']}">View commit</a>
        </div>
    </div>
    """

html_output += """
<hr>
<div class="footer-note">
This page refreshes automatically once per day using GitHub Actions.<br>
Last generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC") + """
</div>

</div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_output)

print("index.html generated successfully 🎉")
