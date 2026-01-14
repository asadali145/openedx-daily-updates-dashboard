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

# JSON data for browser JS
json_data = json.dumps(all_commits)

# ----------- HTML OUTPUT --------------

html_output += """
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<script>
const commits = """ + json_data + """;

function hoursAgo(dateStr) {
  const then = new Date(dateStr);
  const diff = (new Date() - then) / 3600000;
  if (diff < 1) return Math.round(diff * 60) + " minutes ago";
  return Math.round(diff) + " hours ago";
}

function toggleDark() {
  document.body.classList.toggle("dark-mode");
}

function render() {
  const search = document.getElementById("searchBox").value.toLowerCase();
  const author = document.getElementById("authorBox").value.toLowerCase();
  const repo = document.getElementById("repoBox").value.toLowerCase();
  let html = "";

  const grouped = {};

  commits.forEach(c => {
    if (search && !c.message.toLowerCase().includes(search)) return;
    if (author && !c.author.toLowerCase().includes(author)) return;
    if (repo && !c.repo.toLowerCase().includes(repo)) return;

    if (!grouped[c.repo]) grouped[c.repo] = [];
    grouped[c.repo].push(c);
  });

  Object.keys(grouped).forEach(r => {
    html += "<h2>📦 " + r + "</h2>";
    grouped[r].forEach(c => {
      html += `
        <div class="commit">
          <b>${c.message}</b><br>
          👤 ${c.author} — ⏰ ${hoursAgo(c.date)}<br>
          <a href="${c.url}">View commit</a>
        </div>
      `;
    });
  });

  document.getElementById("commits").innerHTML = html;

  const repoCounts = Object.keys(grouped).map(k => grouped[k].length);
  const labels = Object.keys(grouped);

  chart.data.labels = labels;
  chart.data.datasets[0].data = repoCounts;
  chart.update();
}

const ctx = document.getElementById("chart");
const chart = new Chart(ctx, {
  type: 'bar',
  data: {
    labels: [],
    datasets: [{
      label: "Commits",
      data: []
    }]
  },
});

render();
</script>
</body>
</html>
"""


with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_output)

print("Dashboard generated 🎉")
