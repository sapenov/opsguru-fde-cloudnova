# QA record

**Current status:** Independent Claude review completed; see the final section. Earlier attempts below are retained as a chronological record.

## Initial independent Claude review attempt (historical)

On 2026-11-18, Claude Code `2.1.325` was installed and `claude auth status` reported a Bedrock configuration. A scoped review was attempted with `claude -p --bare --tools '' --disable-slash-commands < /tmp/opsguru-claude-review-packet.txt > /tmp/opsguru-claude-review-output.txt 2> /tmp/opsguru-claude-review-error.txt`. The packet contained the review brief, employer briefs, specs, source code, fixture tests, documentation, author-generated demo and test output, Git history, and only the CSV header and first two rows. No tools were exposed to the reviewer, and no keys, correspondence, or unrelated files were included. The process exited 1 with: `API Error: Could not load AWS credentials · Token is expired.` There was no Claude verdict; it is not an independent review. The packet was prepared before the local fixes below, so use the final review bundle instead of that packet for a future review.

For Claude Chat, supply the separately prepared local review bundle and [review prompt](claude-review-prompt.md). The bundle contains the submission repository and full assessment CSV; share it only if authorized. Ask the reviewer to distinguish supplied outputs from checks they personally run. The archive contains no credentials or correspondence.

## Author checks and changes

- `python3 -m unittest discover -s evals -v`: fixture results in [eval output](eval-output.txt). Eight initial checks passed, plus the historical churn expected failure; two subsequent regression tests initially failed, then passed after the author corrected the router and top-account ID. This is author QA, not an independent review.
- `python3 -m app`: six actual dataset outputs and quality counts in [demo output](demo-output.txt).
- A separate raw-CSV Python calculation, without importing application code, independently reproduced 2024 paid cents `3268637120`, refund cents `-193128282` and net cents `3075508838` with the same first-row/date/FX assumptions. This does not independently validate those assumptions or all other full-data metrics.
- Router now accepts only listed question forms, rejecting extra filters rather than silently ignoring them. For a revenue account lacking any valid dated snapshot, the top-account query retains the revenue-side account ID and leaves snapshot fields null.

At that point, the independent Claude review remained outstanding. Remaining limitations include no complete independent reconciliation of all full-data outputs; aggregate rather than per-metric exclusion reporting; fixture coverage does not prove every dirty-data case. See implementation notes for other departures from the pre-build spec.

## Clean-checkout verification and time

`git clone --quiet --no-local . /tmp/opsguru-clean-checkout`, followed there by `python3 -m unittest discover -s evals -v` and `python3 -m app`, completed successfully: 10 checks passed and one was an expected failure. The clean-checkout demo matched the recorded demo byte-for-byte, the CSV hash matched the handoff, and `git status --short` was empty. This verification was performed at commit `5a4cec6`; subsequent changes are documentation and packaging only.

The first recorded shell timestamp was 11:52:10 ET and the clean-checkout verification completed by 11:57:42 ET on November 18, 2026: approximately 5 minutes 32 seconds elapsed for this session's observed work. Active time was not separately instrumented and cannot be stated precisely. The handoff/specification work happened earlier and is not included in this session's elapsed time.

## Retry after SSO refresh

On November 18, the user reported that Claude SSO had been refreshed. A new review was prepared from a scoped copy of this repository with Claude Code's restricted mode, only `Read`, `Glob`, and `Grep` tools, no command execution, and an instruction to avoid sending the full CSV unnecessarily. The first `--bare` attempt did not load the local Bedrock settings and failed with an expired OAuth session. A second attempt loaded only the provider/profile/region settings, but the sandbox could not resolve the AWS SSO hostname (`EAI_AGAIN`). No review output or verdict was produced.

An escalated retry to access AWS SSO and Bedrock was rejected by automatic approval review: the reviewer identified the risk of sending private assessment materials to an externally hosted AWS service and said explicit authorization for that destination was required. It was not retried through another route at that point. The subsequently authorized review is recorded below.

## Completed independent Claude review

After the user explicitly authorized sending scoped assessment materials to the configured AWS Bedrock service, an independent Claude Code review was completed on November 18, 2026. The successful invocation was `claude -p --bare --settings /tmp/opsguru-claude-settings.json --restricted --strict-mcp-config --tools '' --model sonnet --disable-slash-commands < /tmp/opsguru-claude-final-packet.txt > /tmp/opsguru-claude-review-final.txt 2> /tmp/opsguru-claude-review-final.err` from a scoped copy of the repository. The settings contained only provider, profile, region and model settings; no credentials were included in the packet. Claude had no tools and received the employer brief, spec, implementation, fixture tests, docs, supplied test/demo output, Git history, and CSV header plus two example rows. The review was independent of the implementing model, but did not execute code, examine the full CSV, or independently verify clean checkout. Its unedited response is [here](claude-review-2026-11-18.md).

An earlier authorized tool-enabled attempt produced no report and was stopped; the successful smaller-packet invocation exited 0. A separate harmless `ready` prompt confirmed the connection. Claude reported no blocking issue and identified incomplete conflict-row reporting, 612 ambiguous dates, limited AI prompt detail, and aggregate exclusion counts as important concerns.

**Author assessment and response:** The review's statement that no Claude review exists reflects the older QA record in its packet; the review itself now exists. The assessment does not explicitly require a separate Claude review, although the user did request one. The date convention was documented before implementation but is unconfirmed; the claim that ambiguous day/month swaps could change invoice *years* is not supported by the documented formats (the year stays fixed). Month assignment and latest-account snapshots can still change, and finance confirmation remains necessary. The original CSV retained conflicting records, but the absence of an easy report was a genuine spec gap: [conflicting-invoices.csv](conflicting-invoices.csv) now lists every source record for the 43 conflicting IDs. The file is specific to the bundled source; alternate inputs do not automatically produce it. Prompt history is limited to genuine instructions, not fabricated to satisfy the rubric. Per-metric exclusion reporting and finance confirmation remain open.

**Post-review verification:** `python3 -m unittest discover -s evals -v` completed with 10 passed and one expected failure. `python3 -m app` completed, and `cmp docs/demo-output.txt /tmp/opsguru-post-review-demo.txt` confirmed its output was unchanged. The conflict report contains 86 source records covering 43 conflicting IDs.

## Post-assessment quality improvements

At the user's later request, unit tests, pinned Ruff, Pylint and Pyright tooling, and CI were added after the original review. A new test first reproduced a traceback for a truncated CSV row; the CLI now rejects both short and extra-field records with a clear error. The focused tests also cover date and currency parsing, duplicate precedence, snapshot MRR, query-only access, and unsupported questions. The original six-question demo output remained byte-for-byte unchanged in local verification. The independent Claude review predates these changes; it did not review the new code or workflow.
