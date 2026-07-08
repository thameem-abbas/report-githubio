# Report Hub

Static site for hosting and sharing HTML reports via GitHub Pages. Drop a report in, push, and it's live — no manual index maintenance.

**Live site:** https://thameem-abbas.github.io/report-githubio

> **⚠️ PUBLIC REPORTS ONLY**
>
> This site is hosted on GitHub Pages and is **publicly accessible to anyone on the internet**. Do NOT publish reports containing credentials, internal-only URLs, customer data, proprietary benchmarks, or any information that should not be shared outside the organization. If your report contains sensitive data, sanitize it before adding it here.

## How It Works

1. Reports live in `reports/<category>/<YYYY-MM-DD>_<slug>/`
2. A GitHub Action runs on every push to `main`
3. A Python script walks `reports/`, reads metadata, and generates `index.html`
4. GitHub Pages serves the result — searchable, filterable, dark mode

No frameworks, no build tools, no external dependencies. Just Python stdlib + GitHub Actions.

## Adding a Report

```bash
# 1. Create a folder (date prefix is important for sorting)
mkdir -p reports/investigations/2026-07-10_my-report

# 2. Copy your HTML report in
cp ~/path/to/report.html reports/investigations/2026-07-10_my-report/report.html

# 3. (Optional) Add metadata for better display
cat > reports/investigations/2026-07-10_my-report/meta.json << 'EOF'
{
  "title": "My Report Title",
  "description": "One-line summary shown on the index page",
  "tags": ["gpu", "vllm", "debug"],
  "date": "2026-07-10",
  "author": "your-github-username",
  "status": "final"
}
EOF

# 4. Commit and push
git add reports/investigations/2026-07-10_my-report/
git commit -m "Add my report"
git push
```

The site rebuilds automatically in ~30 seconds.

### Without meta.json

If you skip `meta.json`, the generator derives:
- **Title** from the folder name (e.g., `my-report` → "My Report")
- **Date** from the folder prefix (e.g., `2026-07-10`)
- **Category** from the parent directory name

So the bare minimum is: create folder, drop HTML file, push.

## Categories

Reports are organized into directories under `reports/`:

| Category | Purpose |
|----------|---------|
| `ci` | CI/test results (pytest-html, allure, etc.) |
| `investigations` | Debug sessions, root cause analysis |
| `benchmarks` | Performance benchmarks, comparisons |

New categories are created by making a new directory — the generator discovers them automatically.

## meta.json Reference

All fields are optional:

| Field | Default | Description |
|-------|---------|-------------|
| `title` | Derived from folder name | Display title |
| `description` | Empty | One-liner shown on the card |
| `tags` | `[]` | Array of strings for filtering |
| `date` | From folder prefix | ISO date (`YYYY-MM-DD`) |
| `author` | Empty | Who created it |
| `status` | `"final"` | `final`, `draft`, or `archived` |
| `entry` | `"report.html"` | HTML filename if not `report.html` |

## Reports With Multiple Files

Some tools (Allure, guidellm) generate a directory of files, not a single HTML. That works fine — put all files in the report folder and set `"entry": "index.html"` in `meta.json`. Relative paths within the report are preserved.

## Index UI Features

- Full-text search across title, description, tags, author
- Filter by category, tags, and status
- Sort by date or title
- Automatic light/dark mode
- Shows file size per report

## Custom Domain (Optional)

1. Buy a domain
2. Add a DNS CNAME record: `reports` → `<username>.github.io`
3. Put the domain in the `CNAME` file
4. In repo Settings → Pages → Custom domain → enter your domain

## Setting Up Your Own

1. Fork or copy this repo
2. Delete existing reports from `reports/`
3. Update `CNAME` (or delete it to use the default `github.io` URL)
4. In your repo Settings → Pages → Source → select "GitHub Actions"
5. Push to `main` — site goes live

The generator (`_generator/generate_index.py`) and workflow (`.github/workflows/deploy.yml`) work out of the box with no configuration.
