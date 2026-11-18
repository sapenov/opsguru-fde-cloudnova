# Independent Repository Review

## Reproducible Material Issues

### 1. **Missing Referenced File**
**File:** `README.md`, line 48  
**File:** `specs/implementation-notes.md`, lines 9-10  
**Issue:** The conflict report `docs/conflicting-invoices.csv` is referenced in both files but was not included in the supplied review materials. The README states it "shows all source records for those IDs" and implementation notes describe it as "preserv[ing] all original rows for each conflicting ID and their source row numbers." Without this file, reviewers cannot verify the 43 conflicting IDs or examine the competing records.

### 2. **Inadequate AI Direction Documentation**
**File:** `README.md`, line 81  
**File:** `docs/prompt-log.md`, lines 4-5  
**File:** `AGENTS.md`  
**Issue:** The assessment rubric (`source/assessment.md`, lines 53, 71-72) expects to see detailed AI prompting, context-setting, and override judgment as "a first-class artifact." The supplied materials contain only high-level summaries. The prompt log explicitly states "there is no separate hidden author-written prompt history to claim," which conflicts with the rubric requirement to demonstrate AI steering. No `.claude/` directory or equivalent detailed configuration exists. The brief instruction in `AGENTS.md` is too minimal to evaluate how AI was directed through the build.

### 3. **Incomplete MRR Calculation Explanation**
**File:** `README.md`, line 42  
**File:** `app/core.py`, line 215  
**Issue:** The README states "MRR averages include snapshots marked as not churned" but does not explain that accounts with NULL region, NULL mrr_cents, or no valid dated snapshot are excluded from the regional average. The query filters `WHERE churned=0 AND mrr_cents IS NOT NULL AND region IS NOT NULL`, which could exclude a substantial number of accounts. Users cannot determine the denominator for "average MRR per account" without examining the code.

### 4. **Churn Rate Definition Ambiguity**
**File:** `README.md`, line 43  
**File:** `app/core.py`, lines 197-198, 223  
**Issue:** The churn rate explanation says it uses "accounts with a known churn status" but does not state this is based on *latest invoice snapshots only*. An account with multiple historical invoices contributes only one snapshot to the churn denominator. If an account's earlier invoices had different plan values, those don't affect the reported churn rate. The relationship between "latest snapshot" and churn percentage is not explicit in user-facing documentation.

### 5. **Same-Date Snapshot Tie-Breaking Not Disclosed**
**File:** `app/core.py`, line 197  
**File:** `specs/track-b-spec.md`, line 14 (specification only)  
**Issue:** The accounts view sorts by `invoice_date DESC, seq ASC` to select the latest snapshot. If an account has multiple invoices on the same date with different plans or attributes, the first in file order wins. This could affect MRR and churn calculations if subscriptions changed mid-day. The README does not warn users that same-date invoices use source-file ordering as a tie-breaker, though the spec acknowledges it.

## Important Risks

### 1. **Unconfirmed Date Parsing Conventions (612 Ambiguous Dates)**
**Impact:** The bundled data contains 612 ambiguous dates (12.2% of 5,000 invoices). The spec documents slash=month/day/year and hyphen=day-month-year conventions, but these are assumptions, not confirmed with finance. If the actual format differs, revenue figures, account snapshots, and MRR calculations could be materially wrong. The README warns about this (line 50) but the magnitude is substantial.

### 2. **First-Row-Wins Deduplication Without Timestamps**
**Impact:** The data has 43 conflicting invoice IDs with no reliable update timestamp. The first record in source file order is retained, which may not be the correct or latest version. This affects revenue, status, amounts, and account snapshots. The implementation notes acknowledge this (line 2), but any conclusions drawn from these 43 invoices are provisional.

### 3. **Aggregate Exclusion Reporting Only**
**Impact:** Quality counts report totals (e.g., `invalid_usd_amount: 0`, `positive_refunds: 0` from demo output) but do not break down exclusions per metric. Users cannot determine *which specific records* were excluded from revenue vs MRR vs churn calculations. Debugging requires manual CSV inspection or code modification.

### 4. **No Dynamic Conflict Report for Alternate CSVs**
**Impact:** The conflict report is explicitly a "static report for the bundled file" (README line 48). If a user supplies `--csv alternate.csv`, conflicting invoice IDs are counted but not detailed. This limits troubleshooting for new data sources.

### 5. **Snapshot Currency vs Actual Subscription State**
**Impact:** The README states "The latest invoice is only a proxy for an account's current subscription" (line 54). An account's most recent invoice may not reflect their active plan if subscriptions changed or invoices are delayed. MRR and churn metrics are approximations, not authoritative current values.

### 6. **Test Output Presented as Independent Verification**
**Impact:** The QA record (`docs/qa.md`, lines 15-16) states "A separate raw-CSV Python calculation...independently reproduced" revenue figures, but labels this as "author QA, not an independent review." The supplied demo output in `docs/demo-output.txt` is similarly author-generated. Per your instructions, I cannot claim these as my observations; they are provided materials, not external verification.

## Minor Suggestions

### 1. **Test Fixture Documentation Clarity**
**File:** `evals/test_app.py`, lines 6-8  
The comment "annual invoice $1,782" describes theoretical annual billing logic, but the test fixture sets `amount="100"` in EUR (10,800 cents USD). This discrepancy could confuse readers. Clarify that the comment explains MRR calculation principles, not the specific test amounts.

### 2. **Date Ambiguity Test Coverage**
**File:** `evals/test_app.py`, line 39  
The test includes one ambiguous date (`05-01-2024`) but does not test year-boundary cases like `12-01-2024` vs `01-12-2024`, where misinterpretation could shift records between years.

### 3. **Seat and Discount Bounds Validation**
**File:** `app/core.py`, lines 143-148  
The code validates `seats > 0` and `0 ≤ discount ≤ 100` but does not enforce upper bounds on seats (e.g., reject seats > 10,000 as implausible). This is a minor edge case.

### 4. **Email Validation Simplicity**
**File:** `app/core.py`, line 169  
The regex `[^@\s]+@[^@\s]+\.[^@\s]+` is simplistic (rejects `user@localhost`, accepts `user@.com`). Since emails are only counted, not used in metrics, this is acceptable but could be documented.

### 5. **Architecture Diagram Completeness**
**File:** `docs/architecture.md`  
The Mermaid diagram omits error-handling paths, the `checked_rows` CSV validator, and quality counter reporting. A more complete diagram would show validation and rejection flows.

### 6. **Zero-Value Refund Handling**
**File:** `app/core.py`, line 137  
The code treats `cents >= 0` for refunds as invalid, excluding zero-value refunds. Whether a $0.00 refund is meaningful is a business question, but the behavior should be documented.

---

## Positive Findings

- SQL uses parameterized queries and query-only mode after build (line 203)
- Explicit rejection of unsupported questions (lines 258-260) prevents silent misinterpretation
- Expected failure test for historical churn is properly marked (`@unittest.expectedFailure`, line 128)
- Business rules (FX rates, list prices, annual billing) correctly match the brief
- Limitations are honestly disclosed in README and implementation notes
- Independent fixtures with hand-calculated expected values (e.g., EUR 100 → $108.00 = 10,800 cents)
- Git history is chronological (though timestamps not shown in supplied excerpt)

## Skepticism of Prior Reviews

The QA record references a completed Claude review (`docs/claude-review-2026-11-18.md`) but that file was not included in this review bundle. I cannot verify what that review found or whether its concerns were addressed. The QA record states the review "identified incomplete conflict-row reporting, 612 ambiguous dates, limited AI prompt detail, and aggregate exclusion counts as important concerns" (line 36), but the repository already documents the 612 ambiguous dates and aggregate counts as known limitations. The missing conflict CSV file appears to have been added post-review (per implementation notes line 9), though I cannot confirm its contents.
