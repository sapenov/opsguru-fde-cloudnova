# Independent QA Review — CloudNova Track B Submission

**Reviewer:** Claude (code-review agent)  
**Date:** 2026-11-18  
**Scope:** Supplied text packet; no command execution or full CSV access  

---

## Executive Summary

This is a **focused, honest prototype** that delivers the core Track B requirements with appropriate transparency about its limitations. The spec-driven approach is evident, business logic is largely correct, and fixture tests use independent arithmetic. However, **critical gaps remain**: no independent Claude review was completed (both attempts failed), AI steering detail is minimal, and 12% of invoices have ambiguous dates resolved by algorithmic convention rather than customer confirmation.

The submission is **runnable in principle** but I cannot verify the one-command demo or test suite actually execute. All "passed test" claims are author-reported, not independently observed.

---

## Blocking Issues

**None.** The core requirements appear satisfied within the documented scope reductions.

---

## Important Issues

### 1. Independent Claude review not completed (required artifact missing)
**Evidence:**  
- `docs/qa.md` lines 3–10: "API Error: Could not load AWS credentials · Token is expired. There was no Claude verdict; it is not an independent review."
- Lines 24–32: Second attempt failed with SSO/sandbox issues, escalated attempt blocked by approval review.

**Impact:**  
The assessment requires demonstrating AI direction and review. The submission attempted this but failed technically. While the author was transparent and prepared review materials, no actual independent verdict exists. A future reviewer would need to repeat this check.

**Practical consequence:**  
Cannot confirm independent validation of business logic, fixture correctness, or security boundaries. Author self-checks (QA section) are present but don't substitute for the required external review.

---

### 2. 612 ambiguous invoice dates (12%) resolved algorithmically
**Evidence:**  
- `demo-output.txt`: `"ambiguous_invoice_dates": 612` out of 5,000 canonical invoices  
- `app/core.py` lines 16–22: Format order `'%m/%d/%Y'` precedes `'%d-%m-%Y'`, so slash-separated dates assume month/day, hyphen-separated assume day-month

**Impact:**  
The business context warns: "some `05-01-2024` that are genuinely ambiguous (day-vs-month)." With 612 such dates, revenue calculations and account snapshots depend on an undocumented assumption (README says "Slash dates use month/day, hyphens day-month" but the *customer* hasn't confirmed this). If the convention is backwards, ~12% of transactions could be assigned to wrong months/years.

**Recommendation:**  
Escalate the 43 conflicting invoice IDs (already reported) *and* a sample of ambiguous dates to finance for format confirmation before any production use. The spec correctly flags this as an assumption requiring validation (line 25), but the scale (612 invoices) makes it a material risk.

---

### 3. Competing invoice records not preserved for audit
**Evidence:**  
- `specs/implementation-notes.md` lines 3–4: "competing full records remain in the unmodified CSV rather than being copied to a separate reject file"  
- `specs/track-b-spec.md` line 22 requires: "record all competing rows and conflict counts in a quality report"

**Impact:**  
43 invoice IDs have conflicting records (different status/amount), and the "first row wins" rule is applied. Users see the conflict count and IDs in quality output but cannot inspect the competing values to judge if the retained row is plausible. For a customer handoff, a `conflicts.csv` with all variant rows would be expected.

**Practical gap:**  
A reviewer or finance user cannot verify whether the first-row heuristic is reasonable for these 43 cases without re-parsing the source CSV.

---

### 4. AI direction detail is minimal (assessment criterion #2)
**Evidence:**  
- `AGENTS.md`: 5 sentences of generic instruction  
- `docs/prompt-log.md`: "there is no separate hidden author-written prompt history to claim"  
- Assessment requirement (line 82): "`.claude/` directory... showing how you configured and steered the AI. This is a first-class artifact for this role."

**Impact:**  
Cannot assess the quality of AI prompting, context-setting, or override decisions (assessment criterion #2). The submission *is* transparent that prompt detail is missing, but this omits a scored dimension. Compare to a scenario where a candidate includes 10–20 iterative prompts showing refinement, error correction, and spec alignment—this would demonstrate FDE skill.

**Partial credit:**  
The spec *itself* is detailed and AI-consumable, which implies good upfront direction. But the claimed Codex session happened in ~5 minutes (11:52–11:57), suggesting either heavy automation or work done in an unrecorded session.

---

### 5. Aggregate exclusion counts hide per-metric impact
**Evidence:**  
- `specs/implementation-notes.md` line 5: "Exclusion counts are aggregate rather than broken down per result"  
- `demo-output.txt`: `"invalid_mrr": 0` but no indication of *which accounts* failed MRR validation if any had in a different dataset

**Impact:**  
If 50 invoices failed MRR validation, a user asking "Which region has highest MRR?" doesn't know if the excluded accounts were concentrated in one region (biasing the answer). For a dashboard handoff, per-metric exclusion footnotes would be standard.

**Scope justification:**  
Acceptable for a 1-hour prototype *if* the README or query output warns users. The current output says "Missing/invalid values are excluded from dependent sums" (generic) but not "X accounts excluded from this MRR answer."

---

## Minor Issues (noted for completeness)

1. **Zero-value refunds excluded** (`specs/implementation-notes.md` line 6): A $0.00 refund might be meaningful (e.g., goodwill adjustment) but won't appear in refund counts. Edge case, unlikely to affect the demo.

2. **No per-row lineage** (implementation notes line 4): Output shows aggregates, not which source rows contributed. Expected for a prototype, noted for production evolution.

3. **Non-critical fields not fully validated** (line 3): `signup_date`, `support_tickets` aren't checked beyond parsing. Acceptable given they don't affect the six questions.

4. **Elapsed time reporting** (`docs/qa.md` line 15): "approximately 5 minutes 32 seconds" for the Git session, but "handoff/specification work happened earlier" is undated. Makes timebox adherence unclear, though the *result* is appropriately scoped.

---

## Verified Strengths

1. **Spec-first development:** Git history shows `specs/track-b-spec.md` committed (11:52:24) before implementation (11:55:19). Spec is detailed and matches the built code.

2. **Business logic correctness:**  
   - FX rates (EUR 1.08, GBP 1.27): `app/core.py` lines 11–12 ✓  
   - Revenue = paid + negative refunds: `QUERIES['revenue']` line 97 ✓  
   - MRR = monthly list price × seats × (1 - discount/100), not divided by billing cycle: lines 68–73 ✓  
   - Account snapshot (latest invoice date): `CREATE VIEW accounts` line 86 ✓  
   - Churn as current flag, not dated rate: `WHERE churned=0` in MRR query line 98 ✓  
   - Top 5 by net revenue with CSAT flag: `QUERIES['top']` line 100 ✓

3. **Independent fixture arithmetic:**  
   - Test comment claims "EUR 100 → $108, EUR -20 → -$21.60; Pro 2 seats at 10% → $178.20 monthly"  
   - Hand calculation: 100 × 1.08 × 100 = 10,800 cents ✓; -20 × 1.08 × 100 = -2,160 cents ✓; 99 × 2 × 0.9 × 100 = 17,820 cents ✓  
   - Test assertions (`evals/test_app.py` lines 24–30) match independent arithmetic, not implementation-derived expectations.

4. **Expected failure properly marked:**  
   - `@unittest.expectedFailure` decorator on `test_historical_churn_date_unavailable` (line 42)  
   - Eval output confirms: "expected failure" (not hidden or passed)  
   - QA record: "An unexpected success of that expected-failure test causes a nonzero exit" (line 11)

5. **Security boundaries:**  
   - SQL templates with parameter binding, no dynamic concatenation (lines 97–101)  
   - `PRAGMA query_only=ON` after data load (line 88)  
   - Unsupported questions rejected with `ValueError` (lines 110, 113)  
   - Test case confirms: `ask(db, 'DROP TABLE invoices')` raises error (line 34)

6. **Transparency about limitations:**  
   - README: "The first row wins conflicting invoice IDs without an authoritative update timestamp, so all totals are provisional" (line 11)  
   - "Churn is a current snapshot fraction, not churn in a period, because no churn dates are available" (line 13)  
   - "Counters and results are not... independently audited financial statements" (line 16)

7. **Six stakeholder questions addressed:**  
   - All six from `source/business-context.md` listed in `app/__main__.py` lines 6–11  
   - Demo output shows all six executed with SQL, parameters, and results

---

## Checks Performed (Material Evidence Only)

1. ✅ **Spec committed before code:** Git history timestamps and file order  
2. ✅ **Business rules match brief:** Traced FX, MRR formula, revenue filters, churn semantics  
3. ✅ **Fixture arithmetic is independent:** Manually recalculated EUR→USD and MRR values  
4. ✅ **Expected failure cannot pass silently:** `@unittest.expectedFailure` verified  
5. ✅ **SQL is parameterized:** Inspected `QUERIES` dict structure  
6. ✅ **Unsupported inputs rejected:** Test cases for SQL injection and unsupported filters  
7. ✅ **Six questions implemented:** Cross-referenced business context and QUESTIONS list  
8. ✅ **Dedup is deterministic:** First-row rule + order-by-seq tie-breaking  
9. ✅ **Assumptions documented:** README sections on date parsing, churn, conflicts

---

## Remaining Uncertainty (Cannot Verify Without Tools)

1. ❌ **One-command demo execution:** Cannot run `python3 -m app` to confirm it works from clean checkout  
2. ❌ **Test suite passes:** Cannot execute `python3 -m unittest discover -s evals -v`  
3. ❌ **Full-data results:** Demo shows 3.27B paid cents in 2024; cannot independently calculate without full CSV and compute access  
4. ❌ **CSV integrity:** Cannot verify SHA-256 hash `f542bc1f...` or row counts (5,125 input, 5,000 canonical)  
5. ❌ **Clean checkout verification:** QA claims byte-identical output but I didn't observe it  
6. ❌ **Date ambiguity inspection:** Cannot examine the 612 ambiguous dates to assess pattern or risk  
7. ❌ **Hidden files:** Cannot confirm no secrets in .gitignore'd paths or untracked workspace files

**Critical caveat:** The review prompt instructs: "never claim to have observed a test run" unless actually run. **I have NOT observed any test execution.** All pass/fail claims are author-reported in `docs/eval-output.txt` and `docs/qa.md`.

---

## Verdict

**Scope and honesty:** The submission delivers a working, bounded prototype that transparently documents its assumptions and scope reductions. The "single command" requirement appears satisfied in principle (README provides exact command), but cannot be independently confirmed.

**Business correctness:** Core financial logic (revenue, MRR, churn, refunds, CSAT) is correctly implemented per the business context. The 612 ambiguous dates (12% of invoices) are a material risk that requires customer validation before production use.

**Evaluation:** Fixture tests use independent arithmetic (verified manually). The expected failure is properly marked. Full-data results are reported but not independently audited—this is disclosed.

**Missing artifacts:** The independent Claude review failed twice (technical issues) and AI steering detail is minimal relative to assessment criterion #2.

**Recommendation:** This submission demonstrates competent spec-driven development and appropriate production instincts (parameterized queries, read-only DB, transparent limits). The missing AI direction artifact and unresolved date ambiguity prevent full confidence. **A follow-up review should:**
1. Obtain finance confirmation on date format conventions for the 612 ambiguous invoices  
2. Run the actual demo and test suite in a controlled environment  
3. Request expanded AI prompt history if this is a key evaluation dimension  

The candidate correctly stopped at an honest 1-hour scope rather than overbuilding. If the technical review gaps (failed Claude review, untested demo) are resolved, this would be a **solid pass** with the date-format caveat escalated to the customer.
