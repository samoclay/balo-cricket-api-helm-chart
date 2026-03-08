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

## ⛵ Balo Cricket Helm Chart — `0.1.0`

Install or upgrade via the published Helm repository:

```bash
helm repo add balo-cricket https://samoclay.github.io/balo-cricket-api-helm-chart
helm repo update
helm upgrade --install balo-cricket balo-cricket/balo-cricket \
  --version 0.1.0 \
  --set api.secrets.jwtSecret=<your-jwt-secret> \
  --set api.secrets.apiKey=<your-api-key>
```

---

### 📦 Bundled container images

| Service | Image | Version |
|---------|-------|---------|
| 🎨 **Frontend** | `ghcr.io/samoclay/balo-cricket-react-frontend-ui` | `latest` |
| ⚙️ **API** | `ghcr.io/samoclay/balo-cricket-api` | `latest` |

---

### 🔄 What changed in this chart release

- fix: add git pull --rebase origin master before push in chart-release workflow
- chore: update CHANGELOG.md [skip ci]
- chore: update CHANGELOG.md [skip ci]
- fix: use .mjs commitlint config for wagoid v6 compatibility, add continue-on-error for cross-repo image checks
- fix: resolve failing CI checks — JS commitlint config with ignores, GHCR uses GITHUB_TOKEN
- feat: add RELEASE.md management with upstream RELEASE.md / GitHub Release fallback chain
- feat: add helm chart, workflows, configs, and release infrastructure

---

### 🎨 Frontend — what's new in `latest`

_No `RELEASE.md` or GitHub Release found for tag `latest` in [samoclay/balo-cricket-react-frontend-ui](https://github.com/samoclay/balo-cricket-react-frontend-ui). Release notes will appear here once the upstream repo publishes them._

---

### ⚙️ API — what's new in `latest`

_No `RELEASE.md` or GitHub Release found for tag `latest` in [samoclay/balo-cricket-api](https://github.com/samoclay/balo-cricket-api). Release notes will appear here once the upstream repo publishes them._

---

> 📋 Full commit history: [CHANGELOG.md](https://github.com/samoclay/balo-cricket-api-helm-chart/blob/master/CHANGELOG.md)

