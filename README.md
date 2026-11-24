# Project Leonida Intelligence Monitor

A Python 3.11+ GitHub intelligence monitor for the canonical Project Leonida repository and independently maintained community map/GIS sources.

## Monitored sources
- `ProjectLeonida/Leonida` — primary project repository.
- `navanem/gta6-leonida-atlas`, `wpenistone/leonida_gis`, `fbritoferreira/gta6` — independent community sources; no official affiliation is implied.

## Capabilities
- Polls repository metadata, branches, tags, releases, commits, issues, pull requests and comments via the public GitHub REST API.
- Tracks changed file paths for new commits and prioritizes map/GIS, runtime, reverse-engineering, asset and documentation activity.
- Persists event deduplication, HTTP cache and per-branch cursors in SQLite.
- Produces dated Markdown daily/weekly, breaking, map and technical reports plus an append-only changelog.
- GitHub Actions schedule: every 30 minutes, with manual bootstrap support.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
export GITHUB_TOKEN="YOUR_TOKEN"  # optional; improves public API rate limits
python -m leonida_monitor --bootstrap
```
Python 3.11+; no third-party runtime dependencies.

## GitHub Actions
The workflow at `.github/workflows/monitor.yml` uses the repository's `GITHUB_TOKEN` and requests `contents: write` to persist SQLite state and reports. In Settings → Actions → General, enable read/write workflow permissions. The first scheduled run establishes the initial baseline; use Actions → Run workflow with `bootstrap=true` for a deeper historical scan (may consume substantial API quota).

## Trust and limitations
The canonical repository is distinguished from unrelated or independent community GIS projects. Community map data is never presented as official Rockstar or Project Leonida data without explicit first-party evidence. The monitor uses public GitHub API metadata; it does not clone complete git histories, download binary game assets, access private repositories, or scrape wiki content. Initial historical scanning is bounded by configuration and GitHub API rate limits.

See [CHANGELOG.md](CHANGELOG.md), [initial research](reports/archive/2026-11-24-initial-research.md), and `config/repos.json`.
