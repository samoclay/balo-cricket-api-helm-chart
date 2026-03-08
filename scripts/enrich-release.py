#!/usr/bin/env python3
"""
enrich-release.py — builds rich release notes for a balo-cricket chart release.

For each upstream service (frontend + API) the script attempts to source release
information using the following priority chain:

  1. RELEASE.md in the upstream repo at the ref matching the bundled image tag
     (fetched via GitHub Contents API — richest, hand-authored notes)
  2. GitHub Release body for that image tag
     (auto-generated or manually edited release in the upstream repo)
  3. Placeholder message explaining where to find future release notes

Reads locally:
  helm/balo-cricket/Chart.yaml   → chart version
  helm/balo-cricket/values.yaml  → frontend + API image repo and tag

Writes:
  /tmp/release-body.md   → consumed by the workflow to update the GitHub Release
  RELEASE.md             → committed back to master as the repo's own release doc

Required environment variables:
  GH_TOKEN            GitHub token with contents:read on the image repos
  GITHUB_REPOSITORY   Owner/repo of this chart repo (set automatically by GitHub Actions)
"""

import base64
import json
import os
import subprocess
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

try:
    import yaml
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pyyaml"])
    import yaml  # noqa: E402  (re-import after install)

# ── Read chart metadata ────────────────────────────────────────────────────────
chart  = yaml.safe_load(open("helm/balo-cricket/Chart.yaml"))
values = yaml.safe_load(open("helm/balo-cricket/values.yaml"))

chart_version  = chart["version"]
frontend_image = values["frontend"]["image"]["repository"]
frontend_tag   = values["frontend"]["image"]["tag"]
api_image      = values["api"]["image"]["repository"]
api_tag        = values["api"]["image"]["tag"]

# Derive GitHub repo slugs from the GHCR image path.
# e.g. ghcr.io/samoclay/balo-cricket-api → samoclay/balo-cricket-api
frontend_gh_repo = "/".join(frontend_image.split("/")[-2:])
api_gh_repo      = "/".join(api_image.split("/")[-2:])

gh_token     = os.environ["GH_TOKEN"]
gh_repo_full = os.environ["GITHUB_REPOSITORY"]


# ── GitHub API helpers ─────────────────────────────────────────────────────────
def _gh_request(url: str) -> dict | None:
    """
    Make an authenticated GET to the GitHub API.
    Returns the parsed JSON body, or None on any HTTP error.
    """
    req = Request(
        url,
        headers={
            "Authorization": f"Bearer {gh_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read())
    except HTTPError as exc:
        print(f"  ℹ️  GitHub API {exc.code} for {url}")
        return None


def fetch_release_md(gh_repo: str, tag: str) -> str | None:
    """
    Fetch the raw content of RELEASE.md from gh_repo at the given tag ref.
    Returns the decoded text, or None if the file does not exist.
    """
    url = f"https://api.github.com/repos/{gh_repo}/contents/RELEASE.md?ref={tag}"
    data = _gh_request(url)
    if data is None:
        return None

    # The Contents API returns base64-encoded content when encoding == "base64"
    encoding = data.get("encoding", "")
    content  = data.get("content", "")
    if encoding == "base64" and content:
        return base64.b64decode(content).decode("utf-8").strip() or None

    return None


def fetch_github_release_body(gh_repo: str, tag: str) -> str | None:
    """
    Fetch the body text of a GitHub Release for gh_repo@tag.
    Returns the body string, or None if no release exists for that tag.
    """
    url  = f"https://api.github.com/repos/{gh_repo}/releases/tags/{tag}"
    data = _gh_request(url)
    if data is None:
        return None
    return data.get("body", "").strip() or None


def upstream_release_notes(gh_repo: str, tag: str, service_label: str) -> str:
    """
    Return the best available release notes for a service, using the priority chain:
      1. RELEASE.md at the image tag ref
      2. GitHub Release body for the tag
      3. Informational placeholder
    """
    # 1 — RELEASE.md
    notes = fetch_release_md(gh_repo, tag)
    if notes:
        print(f"  ✅ {service_label}: sourced from RELEASE.md @ {tag}")
        return notes

    # 2 — GitHub Release body
    notes = fetch_github_release_body(gh_repo, tag)
    if notes:
        print(f"  ✅ {service_label}: sourced from GitHub Release @ {tag}")
        return notes

    # 3 — Placeholder
    print(f"  ℹ️  {service_label}: no RELEASE.md or GitHub Release found for tag '{tag}'")
    return (
        f"_No `RELEASE.md` or GitHub Release found for tag `{tag}` in "
        f"[{gh_repo}](https://github.com/{gh_repo}). "
        f"Release notes will appear here once the upstream repo publishes them._"
    )


def conventional_commits_since_last_tag() -> str:
    """
    Return a markdown list of conventional commits since the previous chart tag.
    Falls back to a placeholder if no conventional commits are found.
    """
    tags_result = subprocess.run(
        ["git", "tag", "--sort=-version:refname"],
        capture_output=True, text=True,
    )
    chart_tags = [
        t for t in tags_result.stdout.splitlines()
        if t.startswith("balo-cricket-")
    ]

    current_tag = f"balo-cricket-{chart_version}"
    try:
        idx      = chart_tags.index(current_tag)
        prev_tag = chart_tags[idx + 1] if idx + 1 < len(chart_tags) else None
    except ValueError:
        # Current tag doesn't exist yet (release not published) — use the newest existing tag
        prev_tag = chart_tags[0] if chart_tags else None

    log_range = f"{prev_tag}..HEAD" if prev_tag else "HEAD"
    log_result = subprocess.run(
        ["git", "log", "--pretty=format:- %s", log_range],
        capture_output=True, text=True,
    )

    cc_types = (
        "feat", "fix", "helm", "ci", "chore",
        "refactor", "perf", "test", "docs", "style", "revert",
    )
    all_lines  = log_result.stdout.strip().splitlines() if log_result.stdout.strip() else []
    chart_commits = [
        line for line in all_lines
        if any(line.startswith(f"- {t}") for t in cc_types)
    ][:25]

    return "\n".join(chart_commits) if chart_commits else (
        "_No conventional commits recorded since the previous release._"
    )


# ── Fetch upstream release notes using the priority chain ─────────────────────
print(f"Chart {chart_version} | Frontend {frontend_image}:{frontend_tag} | API {api_image}:{api_tag}")
print("Fetching upstream release notes …")

fe_notes_md  = upstream_release_notes(frontend_gh_repo, frontend_tag, "Frontend")
api_notes_md = upstream_release_notes(api_gh_repo,      api_tag,      "API")

chart_changes_md = conventional_commits_since_last_tag()

# ── Assemble the shared release body ──────────────────────────────────────────
body = f"""\
## ⛵ Balo Cricket Helm Chart — `{chart_version}`

Install or upgrade via the published Helm repository:

```bash
helm repo add balo-cricket https://samoclay.github.io/balo-cricket-api-helm-chart
helm repo update
helm upgrade --install balo-cricket balo-cricket/balo-cricket \\
  --version {chart_version} \\
  --set api.secrets.jwtSecret=<your-jwt-secret> \\
  --set api.secrets.apiKey=<your-api-key>
```

---

### 📦 Bundled container images

| Service | Image | Version |
|---------|-------|---------|
| 🎨 **Frontend** | `{frontend_image}` | `{frontend_tag}` |
| ⚙️ **API** | `{api_image}` | `{api_tag}` |

---

### 🔄 What changed in this chart release

{chart_changes_md}

---

### 🎨 Frontend — what's new in `{frontend_tag}`

{fe_notes_md}

---

### ⚙️ API — what's new in `{api_tag}`

{api_notes_md}

---

> 📋 Full commit history: [CHANGELOG.md](https://github.com/{gh_repo_full}/blob/master/CHANGELOG.md)
"""

# ── Write outputs ──────────────────────────────────────────────────────────────
# 1. /tmp/release-body.md — consumed by the workflow to update the GitHub Release
tmp_path = "/tmp/release-body.md"
with open(tmp_path, "w") as f:
    f.write(body)
print(f"GitHub Release body written to {tmp_path} ({len(body)} chars)")

# 2. RELEASE.md — committed back to the repo as the permanent release document.
#    The file accumulates an entry per chart version, newest first.
#    It is idempotent: re-running for the same version replaces the old entry.
import re

release_md_path = "RELEASE.md"

file_header = """\
# 📦 Release Notes — Balo Cricket Helm Chart

This file is auto-generated on every chart release. Each entry documents:
- The Helm chart version published
- The exact frontend and API container image versions bundled
- What changed in this chart release (conventional commits)
- Upstream release notes pulled from each service's own `RELEASE.md` (if present)
  or their GitHub Release body — whichever is richer

The priority chain used to source upstream notes for each service is:

1. **`RELEASE.md`** at the image tag ref in the upstream repo (richest, hand-authored)
2. **GitHub Release body** for that image tag
3. Informational placeholder (if neither exists yet)

---

"""

# Read existing release entries (everything after the fixed file_header,
# excluding any placeholder text added before the first real publish).
previous_entries = ""
if os.path.exists(release_md_path):
    with open(release_md_path) as f:
        raw = f.read()
    # Strip the fixed header block so we are left with only "## ⛵ …" sections.
    # The header ends at the first "## ⛵" or at the "---" separator before it.
    entries_match = re.search(r"(## ⛵ Balo Cricket Helm Chart)", raw)
    if entries_match:
        previous_entries = raw[entries_match.start():]

# Remove any existing entry for this exact chart version (idempotent re-runs).
version_heading = f"## ⛵ Balo Cricket Helm Chart — `{chart_version}`"
if version_heading in previous_entries:
    previous_entries = re.sub(
        rf"{re.escape(version_heading)}.*?(?=\n## ⛵ |\Z)",
        "",
        previous_entries,
        flags=re.DOTALL,
    ).lstrip()

# Build the final file: fixed header + new entry + older entries.
separator   = "\n\n---\n\n"
new_content = (
    file_header
    + body
    + (separator + previous_entries.strip() if previous_entries.strip() else "")
    + "\n"
)

with open(release_md_path, "w") as f:
    f.write(new_content)
print(f"RELEASE.md written ({len(new_content)} chars)")
