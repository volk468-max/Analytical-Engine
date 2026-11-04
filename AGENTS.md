# Repository instructions

## Alpha OS project knowledge (v1)

Before every task:
1. Read docs/alpha-os-knowledge/PROJECT_STATUS.md, DECISIONS.md and NEXT_STEPS.md.
2. Read related research in RESEARCH_INDEX.md and its pinned reports.
3. Identify the actual code branch/commit and dataset manifest/version; main is not proof of deployed production. Verify related GitHub PR state/head. Record unknowns explicitly.
4. Do not repeat research without a stated new question, new data, or correction rationale.

After every task:
1. Update research catalogue, add new confirmed facts and project status changes.
2. Record limitations and open questions, update next steps and CHANGELOG.md.
3. Cite source PRs and full source commit SHAs, dataset hashes where applicable.
4. Preserve historical records/results/cards/snapshots; new result or correction gets a new version and explicit supersedes reference. Refresh mutable status.json and PROJECT_STATUS together.
5. Distinguish facts, hypotheses, recommendations and explicit owner decisions. Never record a Codex proposal as an approved owner decision. Draft or open PR is not deployed functionality.
6. Run python scripts/validate_project_knowledge.py --online --base-ref <PR-base-SHA> and relevant tests. Explain unavailable checks; never fabricate success. Human review must check semantic citations, privacy and licensing; automated scanning is partial.

Documentation updates are part of the task, not a separate autonomous agent. No autonomous production changes, approvals, purchases, merge or deploy. Keep all existing repository instructions when extending this file.
