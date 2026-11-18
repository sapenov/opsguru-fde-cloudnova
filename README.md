# CloudNova: local invoice questions

A focused Track B prototype cleans the supplied invoice ledger into SQLite and answers six bounded stakeholder questions with inspectable SQL and bound parameters. It needs Python 3.9+ and SQLite with window-function support; no packages, credentials or network are needed.

Run all six questions from a clean checkout:

```sh
python3 -m app
```

Ask one supported question with `python3 -m app --question 'Which region has the highest average MRR per account?'`; use `--csv path` for a compatible file. Answers and quality information are JSON-like text. Money and MRR values are **USD cents**; divide by 100. `python3 -m unittest discover -s evals -v` runs fixture checks and one explicitly expected failure. An unexpected success of that expected-failure test causes a nonzero exit.

The deterministic router accepts the six questions printed by the demo and a few explicitly listed wording variants. It is not a general natural-language model. Unsupported questions, including historical churn and arbitrary SQL, are rejected. The query text and parameters are displayed; SQL templates alone execute and SQLite is read-only after loading. The CSV is never sent anywhere by the program.

## Interpretation and limitations

The [pre-build spec](specs/track-b-spec.md) records detailed rules; [changes and gaps](specs/implementation-notes.md) identify departures. Revenue is paid plus negative refunds; the 2024 query shows paid, refunds, and net separately. FX rates are fixed at 1.08 EUR and 1.27 GBP. Account MRR uses USD list price × seats × discount, once per latest dated account snapshot; annual billing does not change MRR. Churn is a **current snapshot fraction**, not churn in a period, because no churn dates are available. The first row wins conflicting invoice IDs without an authoritative update timestamp, so all totals are provisional. Slash dates use month/day, hyphens day-month; ambiguity counts are surfaced. Top accounts use net recognized revenue and snapshot CSAT; missing CSAT is unknown. Pending/failed counts include all such invoices, while exposure sums only valid positive amounts.

The quality output reports data exclusions and conflicting invoice IDs; [competing source rows](docs/conflicting-invoices.csv) are provided for the bundled CSV, with original source row numbers. Amounts with unrecognized currency or conflicting currency marker, invalid invoice dates in date-filtered queries, unknown categories in dependent metrics, invalid MRR inputs and nonnegative refunds are excluded from relevant calculations. The ledger can contain inconsistent snapshots; a latest invoice is not proof of a currently active subscription. Counters and results are not a reconciliation with a source system. A missing account/date cannot form a snapshot. The fixture assertions are independent arithmetic; full-data results are computed outputs, not independently audited financial statements.

With another day: obtain finance decisions on conflicting records and ambiguous dates, reconcile against billing totals, add historical subscription/churn events, evaluate broader language paraphrases, and add stronger per-metric exclusion and lineage reports. See [architecture](docs/architecture.md), [AI direction](AGENTS.md), [prompt log](docs/prompt-log.md), and [QA record](docs/qa.md).

## Developer checks

The application itself still has no third-party runtime dependencies. To install the pinned development tools (Python 3.12 recommended for tooling) and run the same local checks used by CI:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m unittest discover -s evals -v
python -m unittest discover -s tests -v
python -m ruff check .
python -m ruff format --check .
python -m pylint --persistent=no --fail-under=8.0 --fail-on=E,F app evals tests
python -m pyright --warnings
```

The original evaluation suite retains its one expected historical-churn failure. The separate unit tests exercise cleaning, duplicates, account snapshots, query-only access, and malformed input. Ruff, Pylint and Pyright use the repository configuration in `pyproject.toml`; GitHub Actions runs tests and the demo on Python 3.9 and 3.12, plus quality checks on 3.12. These checks and the input-validation fix were added after the original assessment and independent review.
