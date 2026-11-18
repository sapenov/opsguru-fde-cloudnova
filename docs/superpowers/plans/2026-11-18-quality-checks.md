# Repository quality checks implementation plan

**Goal:** Add maintainable unit tests and automated lint, formatting, and type checks while preserving the offline demo.
**Architecture:** Standard-library tests cover cleaning, queries, read-only SQL and CLI failures. Pinned developer tools and GitHub Actions run independently of the no-dependency runtime.
**Spec:** The original `specs/track-b-spec.md` and user-requested practices from DGR Hermes.

1. Test malformed input and the critical currency, deduplication, snapshot, and read-only boundaries. Confirm the malformed-record test fails, then return a clear CLI error.
2. Apply Ruff formatting and selected checks, Pylint's 8.0 floor, and Pyright's standard mode. Add useful annotations where the type checker needs them.
3. Run evaluations, unit tests, the actual demo and all quality commands; document setup and automate the same checks in CI.

Review focus: short and oversized CSV rows, conflicting currency markers, positive refunds, repeated accounts, and unsupported or write queries.
