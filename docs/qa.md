# QA record

## Independent Claude review: attempted, not completed

On 2026-11-18, Claude Code `2.1.325` was installed and `claude auth status` reported a Bedrock configuration. A scoped review was attempted with `claude -p --bare --tools '' --disable-slash-commands < /tmp/opsguru-claude-review-packet.txt > /tmp/opsguru-claude-review-output.txt 2> /tmp/opsguru-claude-review-error.txt`. The packet contained the review brief, employer briefs, specs, source code, fixture tests, documentation, author-generated demo and test output, Git history, and only the CSV header and first two rows. No tools were exposed to the reviewer, and no keys, correspondence, or unrelated files were included. The process exited 1 with: `API Error: Could not load AWS credentials · Token is expired.` There was no Claude verdict; it is not an independent review. The packet was prepared before the local fixes below, so use the final review bundle instead of that packet for a future review.

For Claude Chat, supply the separately prepared local review bundle and [review prompt](claude-review-prompt.md). The bundle contains the submission repository and full assessment CSV; share it only if authorized. Ask the reviewer to distinguish supplied outputs from checks they personally run. The archive contains no credentials or correspondence.

## Author checks and changes

- `python3 -m unittest discover -s evals -v`: fixture results in [eval output](eval-output.txt). Eight initial checks passed, plus the historical churn expected failure; two subsequent regression tests initially failed, then passed after the author corrected the router and top-account ID. This is author QA, not an independent review.
- `python3 -m app`: six actual dataset outputs and quality counts in [demo output](demo-output.txt).
- A separate raw-CSV Python calculation, without importing application code, independently reproduced 2024 paid cents `3268637120`, refund cents `-193128282` and net cents `3075508838` with the same first-row/date/FX assumptions. This does not independently validate those assumptions or all other full-data metrics.
- Router now accepts only listed question forms, rejecting extra filters rather than silently ignoring them. For a revenue account lacking any valid dated snapshot, the top-account query retains the revenue-side account ID and leaves snapshot fields null.

Open: no independent Claude review; no complete independent reconciliation of all full-data outputs; aggregate rather than per-metric exclusion reporting; fixture coverage does not prove every dirty-data case. See implementation notes for other departures from the pre-build spec.

## Clean-checkout verification and time

`git clone --quiet --no-local . /tmp/opsguru-clean-checkout`, followed there by `python3 -m unittest discover -s evals -v` and `python3 -m app`, completed successfully: 10 checks passed and one was an expected failure. The clean-checkout demo matched the recorded demo byte-for-byte, the CSV hash matched the handoff, and `git status --short` was empty. This verification was performed at commit `5a4cec6`; subsequent changes are documentation and packaging only.

The first recorded shell timestamp was 11:52:10 ET and the clean-checkout verification completed by 11:57:42 ET on November 18, 2026: approximately 5 minutes 32 seconds elapsed for this session's observed work. Active time was not separately instrumented and cannot be stated precisely. The handoff/specification work happened earlier and is not included in this session's elapsed time.

## Retry after SSO refresh

On November 18, the user reported that Claude SSO had been refreshed. A new review was prepared from a scoped copy of this repository with Claude Code's restricted mode, only `Read`, `Glob`, and `Grep` tools, no command execution, and an instruction to avoid sending the full CSV unnecessarily. The first `--bare` attempt did not load the local Bedrock settings and failed with an expired OAuth session. A second attempt loaded only the provider/profile/region settings, but the sandbox could not resolve the AWS SSO hostname (`EAI_AGAIN`). No review output or verdict was produced.

An escalated retry to access AWS SSO and Bedrock was rejected by automatic approval review: the reviewer identified the risk of sending private assessment materials to an externally hosted AWS service and said explicit authorization for that destination was required. It was not retried through another route. The independent review remains outstanding.
