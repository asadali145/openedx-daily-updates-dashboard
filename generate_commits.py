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

# Sort newest first
all_commits.sort(key=lambda c: c["date"], reverse=True)

# JSON data for browser JS
json_data = json.dumps(all_commits)

# ----------- HTML OUTPUT --------------

html_output = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Open edX Daily Commits Dashboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<!-- Primer GitHub style -->
<link rel="stylesheet" href="https://unpkg.com/@primer/css/dist/primer.css">

<style>
body {{
    transition: background .3s, color .3s;
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
}}
.commit.dark {{
    border-color: #30363d;
    background: #161b22;
}}
.dark-mode {{
    background: #0d1117;
    color: #e6edf3;
}}
.controls input, .controls select {{
    margin-right: 8px;
    padding: 6px 10px;
    margin-bottom: 8px;
    border-radius: 6px;
    border: 1px solid #d0d7de;
}}
.chart-box {{
    border: 1px solid #d0d7de;
    padding: 10px;
    border-radius: 10px;
    margin-bottom: 20px;
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
    <!-- dropdown for repositories -->
    <select id="repoSelect" onchange="render()">
        <option value="">All repos</option>
        {"".join(f'<option value="{html.escape(repo)}">{html.escape(repo)}</option>' for repo in REPOSITORIES)}
    </select>
    <!-- keep the free-text repo filter -->
    <input id="repoBox" placeholder="Filter repo (text)…" oninput="render()">
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
    const ctx = document.getElementById("chart");
    const chart = new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: [],
            datasets: [{{
                label: "Commits",
                data: [],
                backgroundColor: '#0969da'
            }}]
        }},
    }});

    function hoursAgo(dateStr) {{
        const then = new Date(dateStr);
        const diff = (new Date() - then) / 3600000;
        if (diff < 1) return Math.round(diff * 60) + " minutes ago";
        return Math.round(diff) + " hours ago";
    }}

    window.toggleDark = function() {{
        document.body.classList.toggle("dark-mode");
        document.querySelectorAll(".commit").forEach(el => el.classList.toggle("dark"));
    }}

    window.render = function() {{
        const searchInput = document.getElementById("searchBox");
        const authorInput = document.getElementById("authorBox");
        const repoInput = document.getElementById("repoBox");
        const repoSelect = document.getElementById("repoSelect");

        const search = searchInput ? searchInput.value.toLowerCase() : "";
        const author = authorInput ? authorInput.value.toLowerCase() : "";
        const repoText = repoInput ? repoInput.value.toLowerCase() : "";
        const repoSelected = repoSelect ? repoSelect.value : "";

        let htmlContent = "";
        const grouped = {{}};

        commits.forEach(c => {{
            if (search && !c.message.toLowerCase().includes(search)) return;
            if (author && !c.author.toLowerCase().includes(author)) return;

            // dropdown filter (exact match)
            if (repoSelected && c.repo !== repoSelected) return;

            // free-text repo filter (substring match)
            if (repoText && !c.repo.toLowerCase().includes(repoText)) return;

            if (!grouped[c.repo]) grouped[c.repo] = [];
            grouped[c.repo].push(c);
        }});

        Object.keys(grouped).forEach(r => {{
            htmlContent += "<h2>📦 " + r + "</h2>";
            grouped[r].forEach(c => {{
                htmlContent += `
                    <div class="commit">
                        <b>${{c.message}}</b><br>
                        👤 ${{c.author}} — ⏰ ${{hoursAgo(c.date)}}<br>
                        🔗 <a href="${{c.url}}" target="_blank">View commit</a>
                    </div>
                `;
            }});
        }});

        document.getElementById("commits").innerHTML = htmlContent;

        // Update chart
        const repoCounts = Object.keys(grouped).map(k => grouped[k].length);
        const labels = Object.keys(grouped);
        chart.data.labels = labels;
        chart.data.datasets[0].data = repoCounts;
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
