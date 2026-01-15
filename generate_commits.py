import requests
from datetime import datetime, timedelta, timezone
import os
import html
import json
import re

# ---------------- CONFIG ----------------

REPOSITORIES = [
    "openedx/edx-platform",
    "openedx/frontend-app-learning",
    "openedx/frontend-app-authoring",
    "openedx/frontend-app-discussions",
    "openedx/XBlock",
    "openedx/paragon",
    "openedx/edx-celeryutils",
    "openedx/frontend-base",
    "openedx/frontend-app-ora",
    "openedx/frontend-platform",
    "openedx/frontend-plugin-framework",
    "openedx/frontend-app-gradebook",
]

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

headers = {}
if GITHUB_TOKEN:
    headers["Authorization"] = f"token {GITHUB_TOKEN}"

# Pull commits for the last 1 month
since_time = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

all_commits = []

for repo in REPOSITORIES:
    url = f"https://api.github.com/repos/{repo}/commits"
    params = {"since": since_time, "per_page": 100}
    page = 1
    while True:
        params["page"] = page
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        commits_page = response.json()
        if not commits_page:
            break
        for commit in commits_page:
            all_commits.append({
                "repo": repo,
                "message": commit["commit"]["message"].split("\n")[0],
                "author": commit["commit"]["author"]["name"],
                "date": commit["commit"]["author"]["date"],
                "url": commit["html_url"],
            })
        # Check if there is a next page
        if "Link" in response.headers and 'rel="next"' in response.headers["Link"]:
            page += 1
        else:
            break


# -------- BREAKING CHANGE ANALYSIS --------

def analyze_breaking_changes(commits):

    KEYWORDS = [
        "breaking",
        "breaking change",
        "breaking-change",
        "bc:",
        "[breaking]",
        "deprecated",
        "deprecat",
        "removed",
        "incompatible",
        "migration required",
        "no longer supports",
        "remove",
    ]
    KEYWORDS = [k.lower() for k in KEYWORDS]

    CONVENTIONAL_RE = re.compile(
        r"^[a-z]+(\([^)]+\))?!:|BREAKING CHANGE:",
        re.IGNORECASE | re.MULTILINE,
    )

    def keyword_method(msg):
        msg_l = msg.lower()
        return any(k in msg_l for k in KEYWORDS)

    def conventional_method(msg, body=None):
        if CONVENTIONAL_RE.search(msg):
            return True
        if body and "BREAKING CHANGE:" in body:
            return True
        return False

    for commit in commits:
        methods = []
        msg = commit["message"]

        if keyword_method(msg):
            methods.append("keyword")

        if conventional_method(msg):
            methods.append("conventional")

        commit["is_breaking"] = bool(methods)
        commit["breaking_methods"] = methods


analyze_breaking_changes(all_commits)

all_commits.sort(key=lambda c: c["date"], reverse=True)

json_data = json.dumps(all_commits)

# -------- HTML OUTPUT --------

html_output = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Open edX Commits Dashboard</title>

<link rel="stylesheet" href="https://unpkg.com/@primer/css/dist/primer.css">

<style>

:root {{
  color-scheme: light dark;
}}

body {{
  transition: background .3s, color .3s;
  background: #ffffff !important;
  color: #24292f !important;
}}

body.dark-mode {{
  background: #0d1117 !important;
  color: #c9d1d9 !important;
}}

.container {{
  max-width: 1100px;
  margin: auto;
  padding: 20px;
}}

.commit {{
  border: 1px solid #d0d7de;
  border-radius: 10px;
  padding: 10px 16px;
  margin-bottom: 10px;
  border-left: 6px solid transparent;
  background: #ffffff !important;
  color: #24292f !important;
}}

.commit.breaking {{
  border-left: 6px solid #d73a49;
  background: #fff5f5 !important;
}}

body.dark-mode .commit {{
  border-color: #30363d !important;
  background: #161b22 !important;
  color: #c9d1d9 !important;
}}

body.dark-mode .commit.breaking {{
  border-left: 6px solid #f85149 !important;
  background: #2a1618 !important;
}}

.breaking-badge {{
  display: inline-block;
  background: #d73a49;
  color: #ffffff;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
  margin-right: 6px;
}}

.controls input,
.controls select {{
  margin-right: 6px;
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid #d0d7de;
  background: #ffffff !important;
  color: #24292f !important;
}}

body.dark-mode .controls input,
body.dark-mode .controls select {{
  background: #161b22 !important;
  color: #c9d1d9 !important;
  border: 1px solid #30363d !important;
}}

.repo-select {{
  position: relative;
  display: inline-block;
  min-width: 300px;
  margin: 10px 0;
}}

.repo-select__button {{
  width: 100%;
  text-align: left;
  padding: 8px 12px;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  background: #fff !important;
  color: #24292f !important;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 400px;
}}

body.dark-mode .repo-select__button {{
  background: #161b22 !important;
  color: #c9d1d9 !important;
  border: 1px solid #30363d !important;
}}

.repo-select__dropdown {{
  position: absolute;
  z-index: 1000;
  background: #fff !important;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  margin-top: 2px;
  width: 100%;
  max-height: 220px;
  overflow-y: auto;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}}

body.dark-mode .repo-select__dropdown {{
  background: #161b22 !important;
  border: 1px solid #30363d !important;
}}

.repo-select__dropdown label {{
  display: flex;
  align-items: center;
  padding: 6px 12px;
  cursor: pointer;
  gap: 8px;
}}

.repo-select__dropdown input[type="checkbox"] {{
  margin-right: 8px;
}}

.chart-box {{
  border: 1px solid #d0d7de;
  padding: 10px;
  border-radius: 10px;
}}

body.dark-mode .chart-box {{
  border-color: #30363d !important;
  background: #161b22 !important;
}}

</style>
</head>

<body>

<div class="container">
<h1>🚀 Open edX commits</h1>

<button onclick="toggleDark()" class="btn">🌙 Toggle dark mode</button>

<hr>

<div class="controls">
  <select id="dateFilter" onchange="render()" style="margin-right:6px;padding:6px 10px;border-radius:6px;border:1px solid #d0d7de;">
    <option value="1d">Last 1 day</option>
    <option value="2d">Last 2 days</option>
    <option value="1w">Last 1 week</option>
    <option value="1m" selected>Last month</option>
  </select>
  <input id="searchBox" placeholder="Search keyword…" oninput="render()">
  <input id="authorBox" placeholder="Filter author…" oninput="render()">

  <div class="repo-select" id="repoSelect">
    <button type="button" class="repo-select__button" id="repoSelectBtn" onclick="toggleRepoDropdown()">
      <span id="repoSelectLabel">All repositories</span>
      <span style="float:right;">▼</span>
    </button>
    <div class="repo-select__dropdown" id="repoSelectDropdown" style="display:none;">
      {"".join(f'<label><input type="checkbox" class="repo-checkbox" value="{html.escape(repo)}"{" checked" if repo == "openedx/edx-platform" else ""} onchange="updateRepoSelectLabel();render()"> {html.escape(repo)}</label>' for repo in REPOSITORIES)}
    </div>
  </div>

  <input id="repoBox" placeholder="Repo contains…" oninput="render()">

  <label>
    <input type="checkbox" id="breakingOnly" onchange="render()">
    Show only breaking
  </label>
</div>

<h3>📊 Commit count</h3>
<div class="chart-box">
  <canvas id="chart" height="80"></canvas>
</div>

<h3>🧭 Commits</h3>
<div id="commits"></div>

<p>Last generated: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}</p>

</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<script>
const commits = {json_data};

let chart = null;

// --- Repo select dropdown logic ---
function toggleRepoDropdown() {{
  const dropdown = document.getElementById("repoSelectDropdown");
  dropdown.style.display = dropdown.style.display === "none" ? "block" : "none";
}}

function closeRepoDropdownOnClickOutside(e) {{
  const select = document.getElementById("repoSelect");
  if (!select.contains(e.target)) {{
    document.getElementById("repoSelectDropdown").style.display = "none";
  }}
}}
document.addEventListener("mousedown", closeRepoDropdownOnClickOutside);

function updateRepoSelectLabel() {{
  const checked = Array.from(document.querySelectorAll(".repo-checkbox:checked"));
  const all = document.querySelectorAll(".repo-checkbox").length;
  let label = "";
  if (checked.length === 0) {{
    label = "No repositories";
  }} else if (checked.length === all) {{
    label = "All repositories";
  }} else if (checked.length <= 3) {{
    label = checked.map(x => x.value).join(", ");
  }} else {{
    label = checked.length + " repositories selected";
  }}
  document.getElementById("repoSelectLabel").textContent = label;
}}

// --- End repo select dropdown logic ---

function toggleDark() {{
  document.body.classList.toggle("dark-mode");

  const isDark = document.body.classList.contains("dark-mode");

  if (chart) {{
    chart.options.scales.x.ticks.color = isDark ? "#e5e7eb" : "#111827";
    chart.options.scales.y.ticks.color = isDark ? "#e5e7eb" : "#111827";
    chart.update();
  }}
}}

function hoursAgo(d) {{
  const then = new Date(d);
  const now = new Date();
  const diffMs = now - then;
  const diffHours = diffMs / 3600000;
  if (diffHours < 1) return Math.round(diffHours * 60) + " minutes ago";
  if (diffHours < 24) return Math.round(diffHours) + " hours ago";
  const diffDays = Math.round(diffHours / 24);
  return diffDays + " days ago";
}}

function getDateLimit() {{
  const filter = document.getElementById("dateFilter").value;
  const now = new Date();
  if (filter === "1d") {{
    return new Date(now.getTime() - 1 * 24 * 60 * 60 * 1000);
  }} else if (filter === "2d") {{
    return new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000);
  }} else if (filter === "1w") {{
    return new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  }} else {{
    return new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
  }}
}}

function render() {{

  const search = (document.getElementById("searchBox")?.value || "").toLowerCase();
  const author = (document.getElementById("authorBox")?.value || "").toLowerCase();
  const repoText = (document.getElementById("repoBox")?.value || "").toLowerCase();
  const breakingOnly = document.getElementById("breakingOnly")?.checked;
  const repoCheckboxes = document.querySelectorAll(".repo-checkbox:checked");
  let selectedRepos = Array.from(repoCheckboxes).map(x => x.value);

  const dateLimit = getDateLimit();

  const grouped = {{}};

  commits.forEach(c => {{
    const commitDate = new Date(c.date);

    if (commitDate < dateLimit) return;
    if (search && !c.message.toLowerCase().includes(search)) return;
    if (author && !c.author.toLowerCase().includes(author)) return;
    if (selectedRepos.length && !selectedRepos.includes(c.repo)) return;
    if (repoText && !c.repo.toLowerCase().includes(repoText)) return;
    if (breakingOnly && !c.is_breaking) return;

    if (!grouped[c.repo]) grouped[c.repo] = [];
    grouped[c.repo].push(c);
  }});

  // ---- commits HTML ----
  let html = "";

  Object.keys(grouped).forEach(repo => {{
    html += "<h2>📦 " + repo + "</h2>";

    grouped[repo].forEach(c => {{

      const badge = c.is_breaking
        ? '<span class="breaking-badge">⚠ BREAKING</span>'
        : "";

      const cls = c.is_breaking ? "breaking" : "";

      html += `
        <div class="commit ${{cls}}">
          ${{badge}}<b>${{c.message}}</b><br>
          👤 ${{c.author}} — ⏰ ${{hoursAgo(c.date)}}<br>
          🔗 <a href="${{c.url}}" target="_blank">View commit</a>
        </div>
      `;
    }});
  }});

  document.getElementById("commits").innerHTML = html;

  // ---- chart ----
  const labels = Object.keys(grouped);
  const values = labels.map(r => grouped[r].length);

  if (!chart) {{
    chart = new Chart(document.getElementById("chart"), {{
      type: "bar",
      data: {{
        labels: labels,
        datasets: [{{ label: "Commits", data: values }}]
      }},
      options: {{ responsive: true }}
    }});
  }} else {{
    chart.data.labels = labels;
    chart.data.datasets[0].data = values;
    chart.update();
  }}

}}

updateRepoSelectLabel();
render();

</script>

</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_output)

print("Dashboard generated 🎉")
