# Next milestone: backend v0.1 preparation

## Goal

Prepare and finalize the backend v0.1 release package after real Home Assistant acceptance.

This milestone is release-preparation focused: documentation, behavior contracts, compatibility notes, and final validation for a stable private-use v0.1 backend release.

## Required work

1. Write installation and setup documentation.
2. Document all integration actions and validation behavior.
3. Document entities, attributes, and stable-ID guarantees.
4. Document week boundaries and completion-retention behavior.
5. Document activation versus deletion semantics.
6. Document known limitations and explicit non-goals.
7. Review storage compatibility and upgrade behavior for storage version 1.
8. Set release version and prepare repository packaging artifacts.

## Constraints

- Preserve storage version 1 unless a concrete migration requirement is discovered.
- Do not add an inventory API in this milestone.
- Do not add a WebSocket command in this milestone.
- Do not build the custom card in this repository.
- Keep behavior changes out of scope unless a release-blocking defect is found.

## Validation

Run:

```zsh
./scripts/validate --fix
./scripts/validate
git diff --check
git diff
```

## Done when

- Backend v0.1 documentation is complete and consistent with implemented behavior.
- Release metadata/versioning and packaging are prepared.
- Validation passes without unresolved release-blocking issues.
- Follow-up milestones are clearly recorded in `docs/ROADMAP.md`.
