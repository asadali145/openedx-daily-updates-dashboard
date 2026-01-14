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


# ---------------- BREAKING CHANGE ANALYSIS ----------------

def analyze_breaking_changes(commits):

    keyword_count = 0
    conventional_count = 0
    ai_count = 0

    KEYWORDS = [
        "breaking", "breaking change", "breaking change:", "bc:", "[breaking]",
        "deprecated", "deprecat", "removed", "incompatible",
        "major version", "migration required", "no longer supports"
    ]
    KEYWORDS = [k.lower() for k in KEYWORDS]

    CONVENTIONAL_RE = re.compile(
        r"^[a-z]+(\([^)]+\))?!:|BREAKING CHANGE:", re.IGNORECASE | re.MULTILINE
    )

    def keyword_method(msg):
        msg_l = msg.lower()
        for kw in KEYWORDS:
            if kw in msg_l:
                return True
        return False

    def conventional_method(msg, body=None):
        if CONVENTIONAL_RE.search(msg):
            return True
        if body and "BREAKING CHANGE:" in body:
            return True
        return False

    for commit in commits:
        methods = []
        msg = commit["message"]
        body = None

        if keyword_method(msg):
            methods.append("keyword")
            keyword_count += 1

        if conventional_method(msg, body):
            methods.append("conventional")
            conventional_count += 1

        commit["is_breaking"] = bool(methods)
        commit["breaking_methods"] = methods

    total = sum(1 for c in commits if c.get("is_breaking"))
    print(
        f"{total} commits flagged as breaking (Keyword: {keyword_count}, Conventional: {conventional_count}, AI: {ai_count})"
    )


analyze_breaking_changes(all_commits)

all_commits.sort(key=lambda c: c["date"], reverse=True)

json_data = json.dumps(all_commits)

# ---------------- HTML OUTPUT ----------------

html_output = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Open edX Daily Commits Dashboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<link rel="stylesheet" href="https://unpkg.com/@primer/css/dist/primer.css">

<style>

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
    border-color: #30363d;
    background: #161b22 !important;
    color: #c9d1d9 !important;
}}

body.dark-mode .commit.breaking {{
    border-left: 6px solid #f85149;
    background: #2a1618 !important;
}}

.breaking-badge {{
    display: inline-block;
    background: #d73a49;
    color: #ffffff;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    margin-right: 8px;
    font-weight: bold;
}}

body.dark-mode a {{
    color: #58a6ff !important;
}}

.chart-box {{
    border: 1px solid #d0d7de;
    padding: 10px;
    border-radius: 10px;
}}

</style>
</head>

<body>

<div class="container">

<h1>🚀 Open edX Commits (last 2 days)</h1>

<button onclick="toggleDark()" class="btn">🌙 Toggle Dark Mode</button>

<hr>

<div class="controls">
    <input id="searchBox" placeholder="Search keyword…" oninput="render()">
    <input id="authorBox" placeholder="Filter author…" oninput="render()">
    <input id="repoBox" placeholder="Filter repo…" oninput="render()">

    <label>
        <input type="checkbox" id="breakingOnly" onchange="render()">
        Show only breaking changes
    </label>
</div>

<h3>📊 Commit count by repository</h3>
<div class="chart-box">
    <canvas id="chart" height="80"></canvas>
</div>

<h3>🧭 Commits</h3>
<div id="commits"></div>

<p>Last generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}</p>

</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<script>

document.addEventListener("DOMContentLoaded", function() {{

    const commits = {json_data};

    // restore theme
    const saved = localStorage.getItem("dark-mode-enabled");
    if (saved === "true") {{
        document.body.classList.add("dark-mode");
        document.documentElement.setAttribute("data-color-mode", "dark");
    }}

    window.toggleDark = function() {{
        document.body.classList.toggle("dark-mode");
        const isDark = document.body.classList.contains("dark-mode");
        document.documentElement.setAttribute("data-color-mode", isDark ? "dark" : "light");
        localStorage.setItem("dark-mode-enabled", isDark);
        render();
    }}

    function hoursAgo(dateStr) {{
        const then = new Date(dateStr);
        const diff = (new Date() - then) / 3600000;
        if (diff < 1) return Math.round(diff * 60) + " minutes ago";
        return Math.round(diff) + " hours ago";
    }}

    const ctx = document.getElementById("chart");
    const chart = new Chart(ctx, {{
        type: "bar",
        data: {{
            labels: [],
            datasets: [{{
                label: "Commits",
                data: []
            }}]
        }},
    }});

    window.render = function() {{

        const search = (document.getElementById("searchBox").value || "").toLowerCase();
        const author = (document.getElementById("authorBox").value || "").toLowerCase();
        const repo = (document.getElementById("repoBox").value || "").toLowerCase();
        const breaking = document.getElementById("breakingOnly").checked;

        let grouped = {{}};
        let html = "";

        commits.forEach(c => {{
            if (search && !c.message.toLowerCase().includes(search)) return;
            if (author && !c.author.toLowerCase().includes(author)) return;
            if (repo && !c.repo.toLowerCase().includes(repo)) return;
            if (breaking && !c.is_breaking) return;

            if (!grouped[c.repo]) grouped[c.repo] = [];
            grouped[c.repo].push(c);
        }});

        Object.keys(grouped).forEach(r => {{
            html += "<h2>📦 " + r + "</h2>";
            grouped[r].forEach(c => {{

                let badge = "";
                let cls = "";

                if (c.is_breaking) {{
                    badge = '<span class="breaking-badge">⚠ BREAKING</span>';
                    cls = "breaking";
                }}

                html += `
                    <div class="commit ${cls}">
                        ${badge}<b>${c.message}</b><br>
                        👤 ${c.author} — ⏰ ${hoursAgo(c.date)}<br>
                        🔗 <a href="${c.url}" target="_blank">View commit</a>
                    </div>
                `;
            }});
        }});

        document.getElementById("commits").innerHTML = html;

        const repoCounts = Object.keys(grouped).map(k => grouped[k].length);
        const labels = Object.keys(grouped);

        chart.data.labels = labels;
        chart.data.datasets[0].data = repoCounts;

        // chart dark mode
        if (document.body.classList.contains("dark-mode")) {{
            chart.options.scales = {{
                x: {{ ticks: {{ color: "#c9d1d9" }} }},
                y: {{ ticks: {{ color: "#c9d1d9" }} }}
            }};
        }} else {{
            chart.options.scales = {{
                x: {{ ticks: {{ color: "#24292f" }} }},
                y: {{ ticks: {{ color: "#24292f" }} }}
            }};
        }}

        chart.update();
    }}

    render();
}});
</script>

</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_output)

print("Dashboard generated 🎉")
