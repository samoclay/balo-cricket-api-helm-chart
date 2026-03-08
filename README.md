# 🏏 balo-cricket-api-helm-chart

> Helm chart and publishing pipeline for the Balo Cricket platform — packaged and published independently from the Kubernetes deployment manifests.

This repository contains the **Helm chart** for deploying the Balo Cricket platform (React frontend UI + backend API) to any Kubernetes cluster. Chart releases are published to a GitHub Pages–hosted Helm repository on every merge to `master`.

| Service | Image | What it does |
|---------|-------|--------------|
| 🎨 **Frontend** | `ghcr.io/samoclay/balo-cricket-react-frontend-ui` | React UI served on port 80 |
| ⚙️ **API** | `ghcr.io/samoclay/balo-cricket-api` | Backend REST API served on port 8080 |

Both images are stored in the **GitHub Container Registry (GHCR)**. The chart defaults to `latest` for each image; pin any published version via `--set`.

---

## 📁 Repository structure

```
.
├── helm/
│   └── balo-cricket/            🎯 Helm chart (the publishable artefact)
│       ├── Chart.yaml           chart metadata & version
│       ├── values.yaml          all tuneable defaults
│       └── templates/           Kubernetes resource templates
│           ├── _helpers.tpl
│           ├── namespace.yaml
│           ├── secret.yaml
│           ├── api-deployment.yaml
│           ├── api-service.yaml
│           ├── frontend-deployment.yaml
│           ├── frontend-service.yaml
│           └── ingress.yaml
│
├── scripts/
│   └── enrich-release.py        📝 enriches GitHub Release notes with upstream changelogs
│
├── CHANGELOG.md                 📋 auto-generated from conventional commits
├── cliff.toml                   ⚙️  git-cliff config (drives CHANGELOG)
├── .commitlintrc.yml            📏 conventional commit rules for PRs
│
└── .github/workflows/
    ├── helm-test.yml            🧪 PR: lint + schema validation + image check
    ├── chart-release.yml        🚀 master: package chart + publish to gh-pages + enrich release notes
    ├── changelog.yml            📋 master: auto-update CHANGELOG.md
    └── commitlint.yml           📏 PR: validate commit message format
```

---

## 📦 Using the published Helm repository

Every time a feature branch is merged into **master**, the CI pipeline packages the chart and publishes it to the Helm repository hosted on **GitHub Pages**. The chart version is driven by the `version` field in `helm/balo-cricket/Chart.yaml`.

### Add the Helm repo

```bash
helm repo add balo-cricket https://samoclay.github.io/balo-cricket-api-helm-chart
helm repo update
```

### Browse all available chart versions

```bash
helm search repo balo-cricket --versions
```

### Install

```bash
helm install balo-cricket balo-cricket/balo-cricket \
  --namespace balo-cricket --create-namespace \
  --set api.secrets.jwtSecret=<your-jwt-secret> \
  --set api.secrets.apiKey=<your-api-key>
```

### Pin specific image versions

```bash
helm install balo-cricket balo-cricket/balo-cricket \
  --namespace balo-cricket --create-namespace \
  --set frontend.image.tag=1.2.0 \
  --set api.image.tag=2.0.1 \
  --set api.secrets.jwtSecret=<your-jwt-secret> \
  --set api.secrets.apiKey=<your-api-key>
```

---

## 🔄 CI / CD — how the chart is published

```
Feature branch  ──► PR ──► master merge
                     │              │
                     ▼              ▼
              On every PR:    On every master push:
              ─────────────   ──────────────────────────────────
              commitlint.yml  changelog.yml
              → validates     → git-cliff reads conventional
                all commit      commits → rewrites CHANGELOG.md
                messages        → commits back to master

              helm-test.yml   chart-release.yml
              → helm lint     → ① auto-bump Chart.yaml version
              → kubeconform        (conventional commits → semver)
                (k8s 1.28 +     ② package chart .tgz
                 k8s 1.30)      ③ create GitHub Release
              → docker               balo-cricket-<ver>
                manifest         ④ tag master: chart-v<ver>
                inspect          ⑤ enrich release notes:
                (both images)         • bundled image versions
                                      • upstream changelogs from
                                        balo-cricket-react-frontend-ui
                                        balo-cricket-api
                                  ⑥ push index.yaml → gh-pages
                                     (live Helm repo)
```

### Automatic chart version bumping

`chart-release.yml` reads all conventional commits since the last `balo-cricket-*` tag and determines the semver bump automatically on every merge to `master`:

| Commit type | Version bump |
|-------------|--------------|
| `BREAKING CHANGE` in body, or `feat!:` / `fix!:` etc. | **major** |
| `feat:` | **minor** |
| `fix:`, `helm:`, `chore:`, `ci:`, `docs:`, `refactor:`, `perf:`, `test:`, `style:`, `revert:` | **patch** |

The bumped `Chart.yaml` is committed back to `master` with `[skip ci]` before `chart-releaser` runs, so no manual version bump is needed. A lightweight `chart-v<version>` tag is also created on `master` after each publish so you can check out exactly what was in the chart at any version:

```bash
git checkout chart-v0.2.0
```

`chart-release.yml` is idempotent — it only creates a GitHub Release when it finds a version that doesn't already have one.

### What a GitHub Release looks like

Each chart release automatically includes:

- 📦 **Bundled image versions** — the exact frontend and API image tags this chart was built with
- 🎨 **Frontend changelog** — release notes fetched live from `samoclay/balo-cricket-react-frontend-ui`
- ⚙️ **API changelog** — release notes fetched live from `samoclay/balo-cricket-api`
- 🔄 **Chart changes** — conventional commits since the previous chart tag

---

## 🛠️ Local development

### Prerequisites

| Tool | Install |
|------|---------|
| 🐳 Docker Desktop (with Kubernetes enabled) | [download](https://www.docker.com/products/docker-desktop/) |
| ☸️ kubectl | [install guide](https://kubernetes.io/docs/tasks/tools/) |
| ⛵ Helm 3 | [install guide](https://helm.sh/docs/intro/install/) |

### Install from local chart

```bash
git clone https://github.com/samoclay/balo-cricket-api-helm-chart.git
cd balo-cricket-api-helm-chart

helm install balo-cricket ./helm/balo-cricket \
  --namespace balo-cricket --create-namespace \
  --set api.secrets.jwtSecret=<your-jwt-secret> \
  --set api.secrets.apiKey=<your-api-key>
```

### Uninstall

```bash
helm uninstall balo-cricket -n balo-cricket
kubectl delete namespace balo-cricket
```

---

## 📝 Contributing — Conventional Commits

Every commit must follow the [Conventional Commits](https://www.conventionalcommits.org/) format. The `commitlint.yml` workflow enforces this on every PR.

### Commit types

| Type | When to use |
|------|-------------|
| `feat` | A new feature or user-facing capability |
| `fix` | A bug fix |
| `docs` | Documentation only changes |
| `helm` | Helm chart changes — values, templates, Chart.yaml version bumps |
| `ci` | CI/CD workflow changes |
| `chore` | Maintenance, dependency bumps, housekeeping |
| `refactor` | Code restructure with no behavior change |
| `perf` | Performance improvements |
| `test` | Adding or fixing tests |
| `style` | Formatting / whitespace only |
| `revert` | Reverts a previous commit |

### Examples

```bash
feat: add staging environment values overlay
fix: correct readiness probe path for API container
helm: bump chart version to 0.2.0
docs: add AWS deployment section to README
ci: add trivy image vulnerability scanning
```

---

## 🗺️ Roadmap

- [ ] 🏗️ AWS environment values overlay
- [ ] 🔐 Sealed Secrets / External Secrets Operator integration
- [ ] 📊 Prometheus / Grafana monitoring stack
- [ ] 🔄 Dependabot for automated image tag bumps
