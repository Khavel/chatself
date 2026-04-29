# Repository instructions

- Make the smallest safe change.
- Do not refactor unrelated code.
- Preserve existing architecture and naming conventions.
- Add or update tests when behavior changes.
- Explain assumptions and tradeoffs in the PR description.

## This repository

This is an AI/chat project. Keep prompts, model calls, persistence, and UI/API boundaries separated. Do not introduce new model providers, dependencies, or data retention behavior unless the issue explicitly requires it.

## Issue readiness

Do not start implementation if the issue lacks clear goal, scope in/out, acceptance criteria, and agent instructions.
