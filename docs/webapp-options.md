# Web Application Integration Options

This document outlines preferred approaches for wrapping the existing eduGAIN analysis package in a web application that can optionally retain historical analysis runs. Solutions are listed in order of preference.

## 1. Streamlit Dashboard with Cached Runs

A Streamlit front end provides the fastest path to an interactive web experience while staying entirely in Python. The existing CLI orchestration in `analyze.py` and the reporting utilities under `src/edugain_analysis/formatters/` can be reused directly inside Streamlit callbacks. Streamlit also offers built-in session state and caching, making it easy to toggle advanced options such as URL validation while keeping responsiveness. For optional history, persisted artifacts (CSV, Markdown summaries) can be stored alongside the XDG-aligned cache handling that already exists in `src/edugain_analysis/core/metadata.py`, and surfaced in the UI as downloadable past runs without managing a database.

**Why it fits best**

- Minimal boilerplate: deploy quickly with pure Python and reuse existing analysis functions.
- Tight integration with current report and CSV generation paths for immediate value.
- Lightweight history by persisting generated files in the existing cache hierarchy.

## 2. FastAPI Backend with HTMX/Alpine.js Front End

FastAPI aligns with the project's modern Python stack and makes it straightforward to expose the analysis routines as asynchronous endpoints. Pairing FastAPI with a lightweight frontend stack such as HTMX and Alpine.js keeps the UI reactive without a complex build toolchain. Historical runs can be stored in SQLite via SQLModel or persisted as structured JSON files. FastAPI's dependency injection also simplifies scheduling background tasks (e.g., long URL validation runs) with progress polling.

**Why it is second choice**

- Balanced control over API and UI while remaining relatively lightweight.
- Async support matches network-bound operations like metadata fetches and URL checks.
- Slightly more setup than Streamlit but offers finer control and easier future expansion (auth, APIs).

## 3. Django Application with Celery Workers

For organizations that need robust multi-user access, permissions, and a richer audit trail, Django is an option. The framework supplies authentication, admin dashboards, and ORM-based persistence out of the box. Celery workers can execute the heavier analysis jobs asynchronously, storing results and histories in a relational database. This approach, while powerful, introduces more infrastructure and operational overhead compared to the lighter alternatives above.

**Why it is third choice**

- Comprehensive feature set (auth, admin, ORM) supports enterprise scenarios.
- Celery integration scales out heavy analysis and preserves detailed histories.
- Higher complexity in project setup, deployment, and maintenance relative to other options.

