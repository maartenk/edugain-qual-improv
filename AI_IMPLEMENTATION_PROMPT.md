# Prompt for Implementation Agent

You are an experienced Python engineer tasked with improving the eduGAIN quality analysis toolkit. Use the existing repository to implement the following improvements, ensuring high test coverage and keeping compatibility with the current CLI and FastAPI interfaces.

## Core Refactors
1. **Introduce Typed Result Records**
   - Replace list/dict positional lookups that shuttle metadata results between modules with explicit dataclasses or typed objects. Focus on the flows in:
     - `src/edugain/cli/analyze.py`
     - `src/edugain/web/routes.py`
     - Any helper modules consumed by both layers.
   - Update unit tests to cover the new structures and guarantee backward-compatible serialization for CLI output.

2. **Unify CLI Utilities**
   - Consolidate duplicated logic across standalone scripts such as `analyze.py`, `src/edugain/cli/seccon.py`, `src/edugain/cli/sirtfi.py`, and `src/edugain/cli/broken_privacy.py`.
   - Ensure they share the same configuration loading, caching, and HTTP download helpers provided in `src/edugain/config/settings.py` and related modules.

## Networking & Validation Enhancements
3. **Harden URL Validation**
   - Extend `validate_privacy_url` and related helpers to fall back to `GET` when `HEAD` is blocked.
   - Add configurable retry/backoff behaviour and avoid global `time.sleep` throttling. Centralize concurrency control so parallel callers are not serialized.

4. **Flexible Parallel Validation**
   - Allow `validate_urls_parallel` to accept an existing semaphore or a flag disabling the creation of a new semaphore. Ensure background tasks that already batch requests can opt out of extra throttling.

## Observability
5. **Structured Logging**
   - Replace `print` statements across CLI and web refresh flows with structured logging using the standard library `logging` module. Provide consistent loggers per module and ensure log configuration is centralized.

## Documentation & UX Adjustments
6. **Trim Overly Long CLI Help**
   - Shorten the marketing-heavy CLI epilogues in `src/edugain/cli/__main__.py` (and related help text). Move detailed explanations to `README.md` if needed.

7. **Streamline FastAPI Description**
   - Simplify the FastAPI app description defined in `src/edugain/web/app.py` to remove unimplemented features (e.g., rate limits) and marketing copy. Ensure the OpenAPI output reflects actual behaviour.

## Missing Functionality
8. **Implement API Rate Limiting**
   - Add actual rate limiting to match the documented promises (e.g., integrate SlowAPI or similar). Make sure limits cover import/export endpoints and are configurable.

9. **Reuse Validation Cache in Background Refresh**
   - Update the dashboard refresh workflow so it reuses the shared URL validation cache instead of passing `None`. Review `src/edugain/web/services/refresh.py` and related cache helpers.

10. **Expose Caching to Standalone CLI Tools**
    - Ensure CLI commands that operate independently reuse the shared download/cache utilities, preventing repeated downloads of metadata aggregates.

## Quality Gates
- Update or add tests under `tests/` to cover all new behaviours.
- Run the existing test suite (`pytest`) and linting commands before submitting changes.
- Provide documentation updates (README, docstrings) wherever new configuration options or behaviours are introduced.

Deliver clean commits, descriptive messages, and update `CHANGELOG.md` if present. Coordinate with maintainers if you need clarification.
