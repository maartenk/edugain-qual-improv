# Project Documentation Index

This folder collects supporting documentation for the eduGAIN analysis toolkit. Start here when you need guidance beyond the main `README.md`.

**Quick links**
- `../README.md#-command-reference` — CLI usage summaries and end-user examples.
- `../README.md#-advanced-configuration` — Tunable timeouts, cache windows, and validation thread counts.
- `../README.md#-developer-setup` — How to bootstrap the development toolchain and optional extras.

- `CLAUDE.md` — coding guidelines and workflows for automation agents collaborating on the project.
- `FUTURE_ENHANCEMENTS.md` — roadmap and research ideas under consideration.
- `../Dockerfile` & `../docker-compose.yml` — containerized workflow for running the CLI and tests.
- `../reports/` — generated coverage reports (via `make coverage` or `pytest --cov`).

**Adding new docs**
1. Create a markdown file in this directory (use `TITLE_GOES_HERE.md` naming).
2. Link it in the list above with a one-line summary so searchers know what they will find.
3. If it supplements an existing README section, add a cross-link there as well.
