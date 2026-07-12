# Admin correction manual test

Use this after the backend release candidate is installed in Home Assistant. The card remains in a separate repository; this test validates only the integration contract it consumes.

1. Open an admin WebSocket client and call `chores_manager/inventory`.
2. Select an existing assignment and call `chores_manager/current_week_completions`.
3. Use the response window end as `local_date` in `chores_manager/set_current_week_completion` with `completed: true`.
4. Confirm the response reports `changed: true`, then call the history command again and confirm the returned completion has the chosen assignment ID and date.
5. Confirm the current-day assignment switch and weekly-points sensor update when the selected date is today.
6. Repeat the same completed request and confirm it is a no-op with `changed: false`.
7. Call the correction command with `completed: false`, then confirm the history row is gone and today's live state updates when applicable.
8. Verify a future date and a date before the current Saturday return an error.
9. Delete an assignment that has a current-week completion, then remove that completion with the same assignment ID and date. Confirm a new completion cannot be added for the deleted assignment.
10. Verify a non-admin WebSocket token is rejected.

Do not test corrections against the retained previous week: that interval is intentionally read-only.
