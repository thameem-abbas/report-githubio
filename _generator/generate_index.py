#!/usr/bin/env python3
"""Generate index.html for the report hub from reports/ folder structure."""

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPORTS_DIR = Path("reports")
OUTPUT_FILE = Path("index.html")


def get_repo_url():
    """Detect GitHub repo URL from git remote."""
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return ""
    url = result.stdout.strip()
    # git@github.com:user/repo.git -> https://github.com/user/repo
    m = re.match(r"git@github\.com:(.+?)(?:\.git)?$", url)
    if m:
        return f"https://github.com/{m.group(1)}"
    # https://github.com/user/repo.git -> https://github.com/user/repo
    m = re.match(r"https://github\.com/(.+?)(?:\.git)?$", url)
    if m:
        return f"https://github.com/{m.group(1)}"
    return ""


def get_version_info(path):
    """Get version count and dates from git log for a path."""
    result = subprocess.run(
        ["git", "log", "--follow", "--format=%H %aI", "--", str(path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return {"versions": 1, "last_updated": "", "commits": []}
    lines = [l for l in result.stdout.strip().split("\n") if l]
    commits = []
    for line in lines:
        parts = line.split(" ", 1)
        if len(parts) == 2:
            commits.append({"sha": parts[0][:8], "date": parts[1][:10]})
    return {
        "versions": len(commits),
        "last_updated": commits[0]["date"] if commits else "",
        "commits": commits,
    }


def discover_reports():
    entries = []
    if not REPORTS_DIR.exists():
        return entries
    for category_dir in sorted(REPORTS_DIR.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith("."):
            continue
        category = category_dir.name
        for report_dir in sorted(category_dir.iterdir()):
            if not report_dir.is_dir() or report_dir.name.startswith("."):
                continue
            entry = parse_report(report_dir, category)
            if entry:
                entries.append(entry)
    return entries


def parse_report(report_dir, category):
    meta_path = report_dir / "meta.json"
    meta = {}
    if meta_path.exists():
        with open(meta_path) as f:
            meta = json.load(f)

    entry_file = meta.get("entry", "report.html")
    html_path = report_dir / entry_file
    if not html_path.exists():
        html_files = list(report_dir.glob("*.html"))
        if not html_files:
            return None
        html_path = html_files[0]
        entry_file = html_path.name

    folder_name = report_dir.name
    date_match = re.match(r"(\d{4}-\d{2}-\d{2})[_-](.*)", folder_name)
    if date_match:
        derived_date = date_match.group(1)
        derived_title = date_match.group(2).replace("-", " ").replace("_", " ").title()
    else:
        derived_date = datetime.fromtimestamp(
            html_path.stat().st_mtime, tz=timezone.utc
        ).strftime("%Y-%m-%d")
        derived_title = folder_name.replace("-", " ").replace("_", " ").title()

    size_bytes = sum(f.stat().st_size for f in report_dir.rglob("*") if f.is_file())
    if size_bytes < 1_000_000:
        size_display = f"{size_bytes / 1024:.0f} KB"
    else:
        size_display = f"{size_bytes / 1_000_000:.1f} MB"

    version_info = get_version_info(html_path)

    prev_path = html_path.with_suffix(f".prev{html_path.suffix}")
    has_prev = prev_path.exists()

    return {
        "title": meta.get("title", derived_title),
        "description": meta.get("description", ""),
        "tags": meta.get("tags", []),
        "date": meta.get("date", derived_date),
        "author": meta.get("author", ""),
        "status": meta.get("status", "final"),
        "category": category,
        "path": str(html_path),
        "prev_path": str(prev_path) if has_prev else "",
        "versions": version_info["versions"],
        "last_updated": version_info["last_updated"],
        "folder": str(report_dir),
        "size": size_display,
    }


def render_index(entries):
    entries.sort(key=lambda e: e["date"], reverse=True)
    categories = sorted(set(e["category"] for e in entries))
    all_tags = sorted(set(tag for e in entries for tag in e["tags"]))
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    repo_url = get_repo_url()

    html = INDEX_TEMPLATE.replace("__ENTRIES_JSON__", json.dumps(entries, indent=2))
    html = html.replace("__CATEGORIES_JSON__", json.dumps(categories))
    html = html.replace("__TAGS_JSON__", json.dumps(all_tags))
    html = html.replace("__GENERATED_AT__", generated_at)
    html = html.replace("__REPORT_COUNT__", str(len(entries)))
    html = html.replace("__REPO_URL__", repo_url)

    OUTPUT_FILE.write_text(html)
    print(f"Generated {OUTPUT_FILE} with {len(entries)} reports")


INDEX_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Report Hub</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#fff;--bg-card:#fff;--bg-hover:#f6f8fa;--border:#d0d7de;
  --text:#1f2328;--text-secondary:#656d76;--accent:#0969da;
  --pill-bg:#ddf4ff;--pill-text:#0969da;--pill-active-bg:#0969da;--pill-active-text:#fff;
  --badge-final:#1a7f37;--badge-draft:#9a6700;--badge-archived:#656d76;
  --shadow:0 1px 3px rgba(0,0,0,0.06);
}
@media(prefers-color-scheme:dark){
  :root{
    --bg:#0d1117;--bg-card:#161b22;--bg-hover:#1c2128;--border:#30363d;
    --text:#e6edf3;--text-secondary:#8b949e;--accent:#58a6ff;
    --pill-bg:#1f3a5f;--pill-text:#58a6ff;--pill-active-bg:#58a6ff;--pill-active-text:#0d1117;
    --badge-final:#3fb950;--badge-draft:#d29922;--badge-archived:#8b949e;
    --shadow:0 1px 3px rgba(0,0,0,0.3);
  }
}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--text);line-height:1.5}
.container{max-width:960px;margin:0 auto;padding:1rem}
header{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem;padding:1.5rem 0;border-bottom:1px solid var(--border)}
header h1{font-size:1.5rem;font-weight:600}
.search-box{padding:0.5rem 0.75rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text);font-size:0.875rem;width:280px;max-width:100%}
.search-box:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(9,105,218,0.15)}
.filters{padding:1rem 0;display:flex;flex-direction:column;gap:0.75rem;border-bottom:1px solid var(--border)}
.filter-row{display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap}
.filter-label{font-size:0.75rem;font-weight:600;text-transform:uppercase;color:var(--text-secondary);min-width:80px}
.pill{display:inline-block;padding:0.25rem 0.75rem;border-radius:99px;font-size:0.75rem;font-weight:500;cursor:pointer;border:1px solid transparent;background:var(--pill-bg);color:var(--pill-text);transition:all 0.15s ease;user-select:none}
.pill:hover{opacity:0.85}
.pill.active{background:var(--pill-active-bg);color:var(--pill-active-text)}
.toolbar{display:flex;align-items:center;justify-content:space-between;padding:0.75rem 0}
.counter{font-size:0.875rem;color:var(--text-secondary)}
.sort-select{padding:0.35rem 0.5rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text);font-size:0.8rem}
.cards{display:flex;flex-direction:column;gap:0.75rem;padding-bottom:2rem}
.card{display:block;padding:1rem 1.25rem;border:1px solid var(--border);border-radius:8px;background:var(--bg-card);text-decoration:none;color:inherit;box-shadow:var(--shadow);transition:border-color 0.15s ease,background 0.15s ease}
.card:hover{border-color:var(--accent);background:var(--bg-hover)}
.card-top{display:flex;align-items:center;justify-content:space-between;gap:0.5rem;margin-bottom:0.35rem}
.card-meta{display:flex;align-items:center;gap:0.5rem;font-size:0.75rem;color:var(--text-secondary)}
.category-badge{padding:0.15rem 0.5rem;border-radius:4px;font-size:0.7rem;font-weight:600;text-transform:uppercase;background:var(--pill-bg);color:var(--pill-text)}
.status-badge{padding:0.15rem 0.5rem;border-radius:4px;font-size:0.7rem;font-weight:600;text-transform:uppercase}
.status-final{color:var(--badge-final);border:1px solid var(--badge-final)}
.status-draft{color:var(--badge-draft);border:1px solid var(--badge-draft)}
.status-archived{color:var(--badge-archived);border:1px solid var(--badge-archived)}
.card-title{font-size:1rem;font-weight:600;margin-bottom:0.25rem}
.card-desc{font-size:0.85rem;color:var(--text-secondary);margin-bottom:0.5rem}
.card-bottom{display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;font-size:0.75rem;color:var(--text-secondary)}
.card-tag{padding:0.1rem 0.4rem;border-radius:4px;background:var(--pill-bg);color:var(--pill-text);font-size:0.7rem}
.card-versions{display:flex;align-items:center;gap:0.5rem;font-size:0.7rem;margin-top:0.4rem;padding-top:0.4rem;border-top:1px solid var(--border)}
.card-versions a{color:var(--accent);text-decoration:none}
.card-versions a:hover{text-decoration:underline}
.version-count{color:var(--text-secondary)}
.card-size{margin-left:auto}
footer{text-align:center;padding:1.5rem 0;font-size:0.75rem;color:var(--text-secondary);border-top:1px solid var(--border)}
.empty-state{text-align:center;padding:3rem 1rem;color:var(--text-secondary)}
.empty-state p{font-size:1rem;margin-bottom:0.5rem}
@media(max-width:600px){
  header{flex-direction:column;align-items:stretch}
  .search-box{width:100%}
  .filter-row{flex-direction:column;align-items:flex-start}
}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>Report Hub</h1>
    <input type="text" class="search-box" id="search" placeholder="Search reports..." autocomplete="off">
  </header>

  <div class="filters">
    <div class="filter-row">
      <span class="filter-label">Category</span>
      <div id="category-filters"></div>
    </div>
    <div class="filter-row" id="tag-filter-row" style="display:none">
      <span class="filter-label">Tags</span>
      <div id="tag-filters"></div>
    </div>
    <div class="filter-row">
      <span class="filter-label">Status</span>
      <div id="status-filters"></div>
    </div>
  </div>

  <div class="toolbar">
    <span class="counter" id="counter"></span>
    <select class="sort-select" id="sort">
      <option value="date-desc">Newest first</option>
      <option value="date-asc">Oldest first</option>
      <option value="title-asc">Title A-Z</option>
      <option value="title-desc">Title Z-A</option>
    </select>
  </div>

  <div class="cards" id="cards"></div>

  <footer>Generated __GENERATED_AT__ &middot; __REPORT_COUNT__ reports indexed</footer>
</div>

<script>
const REPORTS = __ENTRIES_JSON__;
const CATEGORIES = __CATEGORIES_JSON__;
const ALL_TAGS = __TAGS_JSON__;
const REPO_URL = "__REPO_URL__";

let activeCategory = null;
let activeTags = new Set();
let searchQuery = "";
let sortBy = "date-desc";
let statusFilter = null;

function init() {
  buildCategoryPills();
  buildTagPills();
  buildStatusPills();
  document.getElementById("search").addEventListener("input", e => {
    searchQuery = e.target.value.trim();
    render();
  });
  document.getElementById("sort").addEventListener("change", e => {
    sortBy = e.target.value;
    render();
  });
  render();
}

function buildCategoryPills() {
  const container = document.getElementById("category-filters");
  const allPill = makePill("All", () => { activeCategory = null; render(); updatePillStates(); });
  allPill.classList.add("active");
  container.appendChild(allPill);
  CATEGORIES.forEach(cat => {
    container.appendChild(makePill(cat, () => {
      activeCategory = activeCategory === cat ? null : cat;
      render(); updatePillStates();
    }));
  });
}

function buildTagPills() {
  if (ALL_TAGS.length === 0) return;
  document.getElementById("tag-filter-row").style.display = "";
  const container = document.getElementById("tag-filters");
  ALL_TAGS.forEach(tag => {
    container.appendChild(makePill(tag, () => {
      activeTags.has(tag) ? activeTags.delete(tag) : activeTags.add(tag);
      render(); updatePillStates();
    }));
  });
}

function buildStatusPills() {
  const container = document.getElementById("status-filters");
  const allPill = makePill("All", () => { statusFilter = null; render(); updatePillStates(); });
  allPill.classList.add("active");
  container.appendChild(allPill);
  ["final", "draft"].forEach(s => {
    container.appendChild(makePill(s, () => {
      statusFilter = statusFilter === s ? null : s;
      render(); updatePillStates();
    }));
  });
}

function makePill(label, onClick) {
  const el = document.createElement("span");
  el.className = "pill";
  el.textContent = label;
  el.addEventListener("click", onClick);
  return el;
}

function updatePillStates() {
  document.querySelectorAll("#category-filters .pill").forEach(p => {
    const isAll = p.textContent === "All";
    p.classList.toggle("active", isAll ? !activeCategory : p.textContent === activeCategory);
  });
  document.querySelectorAll("#tag-filters .pill").forEach(p => {
    p.classList.toggle("active", activeTags.has(p.textContent));
  });
  document.querySelectorAll("#status-filters .pill").forEach(p => {
    const isAll = p.textContent === "All";
    p.classList.toggle("active", isAll ? !statusFilter : p.textContent === statusFilter);
  });
}

function filterReports() {
  return REPORTS.filter(r => {
    if (activeCategory && r.category !== activeCategory) return false;
    if (activeTags.size > 0 && !r.tags.some(t => activeTags.has(t))) return false;
    if (statusFilter && r.status !== statusFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const haystack = [r.title, r.description, r.category, r.author, ...r.tags].join(" ").toLowerCase();
      if (!haystack.includes(q)) return false;
    }
    return true;
  });
}

function sortReports(list) {
  const copy = [...list];
  switch (sortBy) {
    case "date-desc": copy.sort((a, b) => b.date.localeCompare(a.date)); break;
    case "date-asc": copy.sort((a, b) => a.date.localeCompare(b.date)); break;
    case "title-asc": copy.sort((a, b) => a.title.localeCompare(b.title)); break;
    case "title-desc": copy.sort((a, b) => b.title.localeCompare(a.title)); break;
  }
  return copy;
}

function render() {
  const filtered = sortReports(filterReports());
  const container = document.getElementById("cards");
  document.getElementById("counter").textContent =
    filtered.length === REPORTS.length
      ? `${REPORTS.length} reports`
      : `Showing ${filtered.length} of ${REPORTS.length} reports`;

  if (filtered.length === 0) {
    container.innerHTML = '<div class="empty-state"><p>No reports match your filters.</p></div>';
    return;
  }

  container.innerHTML = filtered.map(r => {
    const historyUrl = REPO_URL ? `${REPO_URL}/commits/main/${escHtml(r.folder)}` : "";
    const versionHtml = r.versions > 1 ? `
      <div class="card-versions">
        <span class="version-count">${r.versions} versions</span>
        ${r.prev_path ? `<a href="${escHtml(r.prev_path)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Previous version</a>` : ""}
        ${historyUrl ? `<a href="${historyUrl}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Full history</a>` : ""}
      </div>` : (historyUrl ? `
      <div class="card-versions">
        <span class="version-count">1 version</span>
        ${historyUrl ? `<a href="${historyUrl}" target="_blank" rel="noopener" onclick="event.stopPropagation()">History</a>` : ""}
      </div>` : "");

    return `
    <div class="card" onclick="window.open('${escHtml(r.path)}','_blank')" style="cursor:pointer">
      <div class="card-top">
        <div class="card-meta">
          <span class="category-badge">${escHtml(r.category)}</span>
          <span>${escHtml(r.date)}</span>
          ${r.author ? `<span>&middot; ${escHtml(r.author)}</span>` : ""}
        </div>
        <span class="status-badge status-${escHtml(r.status)}">${escHtml(r.status)}</span>
      </div>
      <div class="card-title">${escHtml(r.title)}</div>
      ${r.description ? `<div class="card-desc">${escHtml(r.description)}</div>` : ""}
      <div class="card-bottom">
        ${r.tags.map(t => `<span class="card-tag">${escHtml(t)}</span>`).join("")}
        <span class="card-size">${escHtml(r.size)}</span>
      </div>
      ${versionHtml}
    </div>`;
  }).join("");
}

function escHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

init();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    entries = discover_reports()
    render_index(entries)
