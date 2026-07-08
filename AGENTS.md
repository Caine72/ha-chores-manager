# Chores Manager agent instructions

## Product scope

Communicate in English.

Chores Manager is a private-use Home Assistant custom integration being prepared for a reliable v0.1 release. Keep changes incremental and optimize the current household workflow before making the integration generic or broadly distributable.

## Architecture invariants

- Integration storage and stable IDs are the source of truth.
- Stable IDs use `kid_*`, `chore_*`, `assignment_*`, and `completion_*` and must never depend on display names or titles.
- Display metadata such as child names, chore titles, categories, points, icons, and active state may change without changing stable identity.
- Completion snapshots are immutable historical records. Metadata edits must not rewrite previously earned points or stored names/titles.
- Entities provide live state and control. The future out-of-repo custom card must be refactored to use stable integration IDs and this repository's integration-aware interface.
- The `Chores` label is a secondary Home Assistant scope boundary for generic automations, templates, filtering, and user organization. It is not the primary card/integration contract. Preserve label-based external targeting; do not replace it with broad domain scans or fragile entity-name matching.
- Deactivation preserves stored objects, registry identity, labels, and history. Explicit delete actions may remove child, chore, and assignment structure, but must preserve immutable completion snapshots until normal retention pruning.
- Existing child, chore, and assignment lifecycle behavior must remain independent.
- Entity IDs and unique IDs must be derived only from stable integration identity, never from mutable child names, chore titles, categories, or other display metadata.
- User-toggleable chore assignments remain switch entities with on/off completion behavior unless the product model is explicitly changed.

## Home Assistant conventions

- Follow current Home Assistant developer patterns and inspect the checked-out Home Assistant Core source when uncertain. For version-sensitive APIs, syntax, deprecations, or frontend behavior, check current official documentation and release notes before changing code.
- Prefer official Home Assistant developer documentation over third-party examples.
- Preserve the config-entry model and `entry.runtime_data` ownership.
- Keep backend state, persistence, validation, and ownership in the integration. Frontend code must not become the long-term business-data store.
- Keep action schemas, constants, `services.yaml`, `strings.json`, `translations/en.json`, and `icons.json` synchronized when actions change.
- Use the repository's current Python syntax. Do not add `from __future__ import annotations`.
- Do not use YAML anchors.

## Development workflow

1. Start from the repository root and inspect `git status` before editing.
2. Do all development work on a separate branch. Bring changes back to `main` only after validation scripts pass and the user explicitly approves.
3. Read `docs/ROADMAP.md` and `docs/NEXT_MILESTONE.md` before starting a milestone.
4. For non-trivial changes, inspect relevant Home Assistant Core implementations and tests, then present a concise plan before coding.
5. Preserve familiar structure and make the smallest change that fully satisfies the milestone.
6. Add focused tests in the same change as production behavior.
7. Run:

   ```zsh
   ./scripts/validate --fix
   ./scripts/validate
   ```

8. Review `git diff --check` and the complete diff before declaring the task done.
9. Report changed files, behavior, tests run, and any unresolved risk.
10. Do not commit, push, rewrite history, or modify unrelated files unless explicitly requested.

## Environment

- Integration repository: `/workspaces/ha-chores-manager`
- Home Assistant Core checkout: `/workspaces/home-assistant-core-dev`
- Integration source: `custom_components/chores_manager`
- Tests: `tests/components/chores_manager`
- Full validation entry point: `./scripts/validate`
- Real HA acceptance automation: `./scripts/run-real-ha-acceptance` (reads local `.real_ha_acceptance.env`)

## Current direction

The next milestone is the backend inventory contract described in `docs/NEXT_MILESTONE.md`. Compare Home Assistant transport options before choosing an interface. Do not build the custom card in this repository; it will live in a separate repository linked later.
