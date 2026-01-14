import requests
from datetime import datetime, timedelta, timezone
import os
import html
import json

# ---------------- CONFIG ----------------

REPOSITORIES = [
    "openedx/edx-platform",
    "openedx/frontend-app-learning",
    "openedx/frontend-app-authoring",
    "openedx/frontend-app-discussions",
]

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# ----------------------------------------

headers = {}
if GITHUB_TOKEN:
    headers["Authorization"] = f"token {GITHUB_TOKEN}"

since_time = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()

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

# Sort newest first
all_commits.sort(key=lambda c: c["date"], reverse=True)

json_data = json.dumps(all_commits)

# ----------- HTML OUTPUT --------------

html_output = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Open edX Recent Commits</title>

<style>
body {
  font-family: Arial, sans-serif;
  background: #f4f4f4;
  margin: 20px;
  color: #222;
}

.dark-mode {
  background: #0f172a;
  color: #e5e7eb;
}

.container {
  max-width: 1100px;
  margin: auto;
}

input {
  padding: 8px;
  margin: 4px;
}

.commit {
  border: 1px solid #ddd;
  padding: 10px;
  margin: 6px 0;
  border-radius: 6px;
}

.dark-mode .commit {
  border-color: #374151;
}

.repo-title {
  margin-top: 20px;
}
</style>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

</head>
<body>
<div class="container">

<h1>📊 Open edX commits (last 2 days)</h1>

<button onclick="toggleDark()">🌓 Toggle dark mode</button>

<br><br>

<input id="searchBox" placeholder="Search message…" oninput="render()">
<input id="authorBox" placeholder="Filter author…" oninput="render()">
<input id="repoBox" placeholder="Filter repo…" oninput="render()">

<canvas id="chart" width="400" height="150"></canvas>

<div id="commits"></div>

</div>

<script>
const commits = """ + json_data + """;

function hoursAgo(dateStr) {
  const then = new Date(dateStr);
  const diffMs = new Date() - then;
  const diffHrs = diffMs / 3600000;

  if (diffHrs < 1) return Math.round(diffHrs * 60) + " minutes ago";
  if (diffHrs < 24) return Math.round(diffHrs) + " hours ago";
  return Math.round(diffHrs / 24) + " days ago";
}

function toggleDark() {
  document.body.classList.toggle("dark-mode");
}

function render() {
  const searchBox = document.getElementById("searchBox");
  const authorBox = document.getElementById("authorBox");
  const repoBox = document.getElementById("repoBox");

  const search = searchBox ? searchBox.value.toLowerCase() : "";
  const author = authorBox ? authorBox.value.toLowerCase() : "";
  const repo = repoBox ? repoBox.value.toLowerCase() : "";

  const grouped = {};

  commits.forEach(c => {
    if (search && !c.message.toLowerCase().includes(search)) return;
    if (author && !c.author.toLowerCase().includes(author)) return;
    if (repo && !c.repo.toLowerCase().includes(repo)) return;

    if (!grouped[c.repo]) grouped[c.repo] = [];
    grouped[c.repo].push(c);
  });

  let html = "";

  Object.keys(grouped).forEach(r => {
    html += "<h2 class='repo-title'>📦 " + r + "</h2>";

    grouped[r].forEach(c => {
      html += `
        <div class="commit">
          <b>${c.message}</b><br>
          👤 ${c.author} — ⏰ ${hoursAgo(c.date)}<br>
          🔗 <a href="${c.url}" target="_blank">View commit</a>
        </div>
      `;
    });
  });

  document.getElementById("commits").innerHTML = html;

  // ---- chart ----
  const labels = Object.keys(grouped);
  const repoCounts = labels.map(k => grouped[k].length);

  chart.data.labels = labels;
  chart.data.datasets[0].data = repoCounts;
  chart.update();
}

document.addEventListener("DOMContentLoaded", function () {
  render();
});

const ctx = document.getElementById("chart");
const chart = new Chart(ctx, {
  type: 'bar',
  data: {
    labels: [],
    datasets: [{
      label: "Commits (last 2 days)",
      data: []
    }]
  }
});
</script>

</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_output)

print("Dashboard generated 🎉")
