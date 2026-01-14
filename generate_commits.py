import requests
from datetime import datetime, timedelta, timezone
import os
import html
import json
import re
import time

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

def analyze_breaking_changes(commits):
    """
    For each commit, set:
      - commit["is_breaking"]: True/False
      - commit["breaking_methods"]: list of method names that flagged it
    Returns summary counts for logging.
    """
    keyword_count = 0
    conventional_count = 0
    ai_count = 0

    # --- Keyword-based analysis ---
    KEYWORDS = [
        "breaking", "breaking change", "breaking change:", "bc:", "[breaking]",
        "deprecated", "deprecat", "removed", "incompatible",
        "major version", "migration required", "no longer supports"
    ]
    KEYWORDS = [k.lower() for k in KEYWORDS]

    # --- Conventional Commits regex ---
    CONVENTIONAL_RE = re.compile(
        r"^[a-z]+(\([^)]+\))?!:|BREAKING CHANGE:", re.IGNORECASE | re.MULTILINE
    )

    # --- GitHub Models API setup ---
    GITHUB_MODELS_API = "https://models.inference.ai.azure.com/chat/completions"
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    AI_HEADERS = {
        "Authorization": f"Bearer {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
        "Content-Type": "application/json"
    }
    AI_MODEL = "gpt-4o-mini"
    AI_PROMPT = "Analyze if this commit might contain breaking changes. Reply with only 'yes' or 'no'."

    def keyword_method(msg):
        msg_l = msg.lower()
        for kw in KEYWORDS:
            if kw in msg_l:
                return True
        return False

    def conventional_method(msg, body=None):
        # Check for ! in type (e.g., feat!:) or BREAKING CHANGE: in body
        if CONVENTIONAL_RE.search(msg):
            return True
        if body and "BREAKING CHANGE:" in body:
            return True
        return False

    def ai_method(msg, body=None):
        # Use GPT-4o-mini via GitHub Models API (free tier)
        if not GITHUB_TOKEN:
            return False  # Can't call API without token
        try:
            payload = {
                "model": AI_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a commit message analyzer."},
                    {"role": "user", "content": f"{AI_PROMPT}\nCommit message: {msg}"}
                ],
                "max_tokens": 3,
                "temperature": 0.0,
            }
            resp = requests.post(
                GITHUB_MODELS_API,
                headers=AI_HEADERS,
                json=payload,
                timeout=1.0
            )
            if resp.status_code != 200:
                return False
            data = resp.json()
            answer = ""
            # Try to extract the model's reply
            if "choices" in data and data["choices"]:
                answer = data["choices"][0].get("message", {}).get("content", "")
            if not answer:
                answer = resp.text
            if "yes" in answer.lower():
                return True
        except Exception:
            # On error (timeout, rate limit, etc), skip AI
            return False
        return False

    for commit in commits:
        methods = []
        msg = commit["message"]
        body = None  # Not available in current data, could be extended

        # a) Keyword-based
        if keyword_method(msg):
            methods.append("keyword")
            keyword_count += 1

        # b) Conventional Commits
        if conventional_method(msg, body):
            if "conventional" not in methods:
                methods.append("conventional")
                conventional_count += 1

        # c) AI (only if not already flagged)
        ai_flagged = False
        if GITHUB_TOKEN and not methods:
            ai_flagged = ai_method(msg, body)
            if ai_flagged:
                methods.append("ai")
                ai_count += 1

        commit["is_breaking"] = bool(methods)
        commit["breaking_methods"] = methods

    total = sum(1 for c in commits if c.get("is_breaking"))
    print(
        f"{total} commits flagged as breaking (Keyword: {keyword_count}, Conventional: {conventional_count}, AI: {ai_count})"
    )

# --- Breaking change analysis ---
analyze_breaking_changes(all_commits)

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
    border-left: 6px solid transparent;
    background: #fff;
}}
.commit.breaking {{
    border-left: 6px solid #d73a49;
    background: #fff5f5;
}}
.commit.dark {{
    border-color: #30363d;
    background: #161b22;
}}
.commit.breaking.dark {{
    border-left: 6px solid #f85149;
    background: #2a1618;
}}
.breaking-badge {{
    display: inline-block;
    background: #d73a49;
    color: #fff;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    margin-right: 8px;
    vertical-align: middle;
    font-weight: bold;
    letter-spacing: 0.5px;
}}
.controls input, .controls select {{
    margin-right: 8px;
    padding: 6px 10px;
    margin-bottom: 8px;
    border-radius: 6px;
    border: 1px solid #d0d7de;
}}
.controls label {{
    margin-right: 12px;
    font-weight: normal;
    font-size: 15px;
    vertical-align: middle;
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
    <select id="repoSelect" multiple size="4" style="vertical-align:middle; min-width:220px;" onchange="render()">
        <option value="">All repos</option>
        {"".join(f'<option value="{html.escape(repo)}">{html.escape(repo)}</option>' for repo in REPOSITORIES)}
    </select>
    <input id="repoBox" placeholder="Filter repo (text)…" oninput="render()">
    <label>
        <input type="checkbox" id="breakingOnly" onchange="render()" style="vertical-align:middle;">
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
        document.querySelectorAll(".commit.breaking").forEach(el => el.classList.toggle("dark"));
    }}

    window.render = function() {{
        const searchInput = document.getElementById("searchBox");
        const authorInput = document.getElementById("authorBox");
        const repoInput = document.getElementById("repoBox");
        const repoSelect = document.getElementById("repoSelect");
        const breakingOnly = document.getElementById("breakingOnly");

        const search = searchInput ? searchInput.value.toLowerCase() : "";
        const author = authorInput ? authorInput.value.toLowerCase() : "";
        const repoText = repoInput ? repoInput.value.toLowerCase() : "";
        const showBreaking = breakingOnly && breakingOnly.checked;

        // Get selected repos (ignore "All repos" if nothing else selected)
        let selectedRepos = Array.from(repoSelect.selectedOptions)
            .map(opt => opt.value)
            .filter(v => v); // remove empty string

        let htmlContent = "";
        const grouped = {{}};

        commits.forEach(c => {{
            if (search && !c.message.toLowerCase().includes(search)) return;
            if (author && !c.author.toLowerCase().includes(author)) return;

            // multi-select filter (exact match, allow multiple)
            if (selectedRepos.length && !selectedRepos.includes(c.repo)) return;

            // free-text repo filter (substring match)
            if (repoText && !c.repo.toLowerCase().includes(repoText)) return;

            // breaking filter
            if (showBreaking && !c.is_breaking) return;

            if (!grouped[c.repo]) grouped[c.repo] = [];
            grouped[c.repo].push(c);
        }});

        Object.keys(grouped).forEach(r => {{
            htmlContent += "<h2>📦 " + r + "</h2>";
            grouped[r].forEach(c => {{
                let breakingBadge = "";
                let breakingClass = "";
                if (c.is_breaking) {{
                    breakingBadge = '<span class="breaking-badge">⚠️ BREAKING</span>';
                    breakingClass = "breaking";
                }}
                htmlContent += `
                    <div class="commit ${{breakingClass}}">
                        ${{breakingBadge}}<b>${{c.message}}</b><br>
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
