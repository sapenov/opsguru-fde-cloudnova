# CloudNova invoice questions

CloudNova is a fictional subscription business with a messy invoice export. This local tool cleans that export and answers six questions about revenue, customers, and unpaid invoices. Each answer includes the SQL query and its parameters, so you can see how it was calculated.

The tool uses Python and an in-memory SQLite database. It needs Python 3.9 or newer and SQLite with window-function support. Running the demo requires no third-party packages, credentials, or network connection.

## Try it

From the repository root, run all six questions:

```sh
python3 -m app
```

To ask one supported question, use:

```sh
python3 -m app --question 'Which region has the highest average MRR per account?'
```

Use `--csv path/to/invoices.csv` to supply another file with the required columns. The output starts with data-quality counts and assumptions, followed by the question, SQL, parameters, column names, and results. Money and monthly recurring revenue (MRR) are reported in **US cents**; divide by 100 to get dollars. An average may contain a fraction of a cent.

The question interface matches a small, fixed set of wordings. It is not a general-purpose language model: questions outside that set are rejected. It runs fixed SQL templates with bound parameters against a database set to query-only after loading; it does not execute SQL supplied by the user.

## Questions it answers

The default demo asks these questions:

1. What was our total recognized revenue in USD for paid invoices in 2024?
2. Which region has the highest average MRR per account?
3. How much have we given back in refunds?
4. What's the churn rate among Enterprise accounts vs Starter?
5. List the top 5 accounts by revenue, and flag any with CSAT ≤ 2.
6. How many invoices are stuck in pending/failed and what's the exposed $?

The first question returns three figures: paid revenue, the signed refund adjustment, and their net total. That question also accepts another year from 1900 through 2099. The other questions use all available invoice dates or the latest account snapshot, as described below.

## How the numbers are calculated

- **Revenue:** Paid invoices count as revenue; negative refunds reduce it. Pending, failed, and void invoices do not count. The 2024 answer filters by invoice date.
- **Currency:** Invoice amounts are converted to US dollars using fixed rates of 1 EUR = 1.08 USD and 1 GBP = 1.27 USD. Each converted invoice is rounded to the nearest cent.
- **MRR:** For each active account, monthly list price per seat is multiplied by seats and the remaining share after discount. List prices are $49 for Starter, $99 for Pro, and $299 for Enterprise. Annual invoices bill for 10 months, but an annual subscription's MRR is still its monthly price; the annual invoice amount is not divided into MRR.
- **Accounts and churn:** For account-level questions, the latest invoice with a valid date supplies one snapshot per account. MRR averages include snapshots marked as not churned. The churn comparison divides churned accounts by accounts with a known churn status in each plan. This is a snapshot, not a churn rate for a specific period: the data has no churn dates.
- **Top accounts and exposure:** Accounts are ranked by paid revenue plus negative refunds, and the latest snapshot supplies customer satisfaction (CSAT). A missing score is unknown. Pending/failed exposure sums valid positive invoice amounts; its invoice count includes pending and failed records even when an amount cannot be summed.

## Data quality and limits

The export contains duplicate invoice IDs without a reliable update timestamp. The first record in the source file wins; it is not necessarily the correct one. The bundled data has 82 exact duplicate rows and 43 IDs with conflicting records. The [conflict report](docs/conflicting-invoices.csv) shows all source records for those IDs; it is a static report for the bundled file, not a report generated for replacement files.

Dates with slashes are read as month/day/year; day-month-year dates with hyphens are read as day/month/year. Some dates could mean either order. The bundled data has 612 such ambiguous invoice dates, and the choice can affect account snapshots and date-based results. Confirm the intended formats with finance before relying on the numbers.

The tool counts data-quality issues and leaves invalid values out of calculations that depend on them. For example, it excludes an amount if its currency is unknown or conflicts with a currency marker, and excludes nonnegative refund amounts from refund totals. The counts are aggregate, not a complete explanation of exclusions for each answer. Invalid dates cannot be used in date-filtered results or account snapshots. Unknown plan, status, churn, or pricing values can exclude records from the relevant metrics.

The latest invoice is only a proxy for an account's current subscription. The ledger does not establish a cancellation date or guarantee that a snapshot is current. Results depend on the duplicate and date choices and have not been reconciled with a billing system. For another day's work, confirm those choices with finance, reconcile totals, add dated subscription events, and report exclusions and source records for each answer.

## Tests and developer checks

The app itself has no third-party runtime dependencies. For development, create a virtual environment using Python 3.12 and install the pinned tools; GNU Make provides shortcuts:

```sh
python3 -m venv .venv
. .venv/bin/activate
make setup
make all
```

`make all` runs both test suites, Ruff, Pylint, a formatting check, Pyright, and the demo without changing files. The evaluation suite includes an **expected failure** for historical churn because the data does not contain churn dates. An unexpected success of that case makes the test command fail so the limitation must be reviewed.

```sh
make test          # Run evaluations and unit tests
make format        # Apply safe Ruff fixes and formatting
make format-check  # Check formatting without changing files
make lint          # Run Ruff and Pylint
make typecheck     # Run Pyright
make demo          # Print all six demo answers
make help          # List targets
```

Make uses `python3` from the active environment; override it with `make PYTHON=/path/to/python all`. The demo can also be run without Make using `python3 -m app`.

For implementation details and the evidence behind the work, see the [business briefing](source/business-context.md), [pre-build specification](specs/track-b-spec.md), [implementation notes](specs/implementation-notes.md), [architecture](docs/architecture.md), [AI instructions](AGENTS.md), [prompt log](docs/prompt-log.md), and [QA record](docs/qa.md).
