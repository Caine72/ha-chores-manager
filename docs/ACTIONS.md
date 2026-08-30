# Home Assistant actions

Actions are available under the `chores_manager` domain.

| Action | Required fields | Optional fields | Behavior |
| --- | --- | --- | --- |
| `add_child` | `name` | `person_entity_id` | Creates an active child and weekly-points sensor. |
| `update_child` | `child_id`, `name` | `person_entity_id` | Updates display metadata without changing stable identity or history. Omit the Person field to preserve it; pass `null` to clear it. |
| `set_child_active` | `child_id`, `active` | none | Deactivates or reactivates a child. |
| `delete_child` | `child_id` | none | Deletes child structure and related registry entries while preserving retained completion snapshots. |
| `add_chore` | `title`, `category`, `points` | `icon`, `sort_order`, `child_ids` | Creates a chore and optional assignments. Omission of `child_ids` assigns all active children. |
| `update_chore` | `chore_id` | `title`, `category`, `points`, `icon`, `sort_order` | Updates future chore presentation and completion metadata. |
| `set_chore_active` | `chore_id`, `active` | none | Deactivates or reactivates a chore. |
| `delete_chore` | `chore_id` | none | Deletes chore structure and related registry entries while preserving retained completion snapshots. |
| `add_assignment` | `child_id`, `chore_id` | none | Assigns one active chore to one active child. |
| `assign_chores_to_child` | `child_id`, `chore_ids` | none | Atomically assigns multiple eligible chores. |
| `remove_chores_from_child` | `child_id`, `chore_ids` | none | Atomically removes multiple assignments while preserving history. |
| `set_assignment_active` | `assignment_id`, `active` | none | Deactivates or reactivates an assignment. |
| `delete_assignment` | `assignment_id` | none | Deletes an assignment and its registry entry while preserving history. |
| `complete_chore_manually` | `chore_id` | none | Completes today's shared chore without assigning a child or awarding points. |
| `reset_manual_chore_completion` | `chore_id` | none | Removes today's manual completion without removing a child claim. |
| `increment_weekly_counter` | `child_id` | `amount`, `reason` | Adds `1-100` points to the current chore week. |
| `decrement_weekly_counter` | `child_id` | `amount`, `reason` | Subtracts `1-100` points without allowing the total below zero. |

Names, titles, and categories are trimmed and limited to 100 characters. Points and adjustment amounts are limited to `1-100`; sort order must be non-negative; icons use Home Assistant's icon format.

User-originated weekly-counter calls require `control` permission for the child's weekly-points sensor. Trusted internal calls without a user context remain available to automations.

Manual completion accepts active shared chores with at least one active assignment.
It creates one zero-point daily occurrence and exposes `completed_manually` on
every synchronized assignment switch. Repeating either manual action is safe.
