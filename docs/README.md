# Project Documentation Index

This folder collects supporting documentation for the eduGAIN analysis toolkit. Start here when you need guidance beyond the main `README.md`.

**Quick links**
- `../README.md#-command-reference` — CLI usage summaries and end-user examples.
- `../README.md#-advanced-configuration` — Tunable timeouts, cache windows, and validation thread counts.
- `../README.md#-developer-setup` — How to bootstrap the development toolchain and optional extras.

- `CLAUDE.md` — coding guidelines and workflows for automation agents collaborating on the project.
- `WEB_INTERFACE_MVP.md` — history and scope of the web interface MVP.
- `FUTURE_ENHANCEMENTS.md` — roadmap and research ideas under consideration.
- `../Dockerfile` & `../docker-compose.yml` — containerized workflow for running the CLI and tests.
- `../scripts/app/` — wrapper entry points for running the CLI without installation.
- `../scripts/dev/` — developer tooling (env bootstrap, linting, local CI, Docker helpers).
- `../scripts/maintenance/` — cache and environment cleanup utilities.
- `../artifacts/coverage/` — generated coverage reports (via `make coverage` or `pytest --cov`).
- `../reports/` — scratch area for CLI exports, downloaded metadata snapshots, etc.

**Adding new docs**
1. Create a markdown file in this directory (use `TITLE_GOES_HERE.md` naming).
2. Link it in the list above with a one-line summary so searchers know what they will find.
3. If it supplements an existing README section, add a cross-link there as well.
