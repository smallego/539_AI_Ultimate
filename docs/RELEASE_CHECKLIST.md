# GitHub Release Checklist

## Before Tagging

- [ ] Confirm `CHANGELOG.md` has the release notes.
- [ ] Confirm `ROADMAP.md` reflects the next milestones.
- [ ] Run `python -m compileall core web tests`.
- [ ] Run `python -m pytest tests`.
- [ ] Run `python -m ruff check .`.
- [ ] Run `python -m black --check .`.
- [ ] Confirm Docker starts with `docker compose up --build`.
- [ ] Confirm `/dashboard`, `/prediction`, `/decision`, `/learning`, `/backtest`, `/data`, and `/settings`.
- [ ] Confirm `/api/health` returns expected health keys.
- [ ] Confirm no database, report, log, or local cache files are staged.

## GitHub Release

- [ ] Create a version tag.
- [ ] Create a GitHub Release from the tag.
- [ ] Paste release highlights from `CHANGELOG.md`.
- [ ] Attach screenshots if available.
- [ ] Mark as pre-release if it is an RC build.

## After Release

- [ ] Open issues for remaining roadmap items.
- [ ] Verify CI badge is green.
- [ ] Archive release artifacts if needed.
