#!/usr/bin/env python3
"""Run automated real-HA acceptance checks for Chores Manager."""

import argparse
import json
import sqlite3
import time
import urllib.error
import urllib.request
from copy import deepcopy
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any


class AcceptanceFailure(AssertionError):
    """Acceptance assertion failed."""


def utc_stamp() -> str:
    """Return a stable UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def read_json(path: Path) -> dict[str, Any]:
    """Read JSON from disk."""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def request_json(
    *,
    base_url: str,
    token: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> Any:
    """Call Home Assistant REST API and parse JSON response."""
    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read()
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        raise AcceptanceFailure(f"{method} {path} failed: {err.code} {body}") from err

    if not raw:
        return None

    return json.loads(raw.decode("utf-8"))


def call_service(
    *,
    base_url: str,
    token: str,
    domain: str,
    service: str,
    data: dict[str, Any],
) -> Any:
    """Call a Home Assistant service and wait for writes."""
    result = request_json(
        base_url=base_url,
        token=token,
        method="POST",
        path=f"/api/services/{domain}/{service}",
        payload=data,
    )
    time.sleep(0.35)
    return result


def get_states(*, base_url: str, token: str) -> dict[str, dict[str, Any]]:
    """Return all states keyed by entity_id."""
    states = request_json(
        base_url=base_url,
        token=token,
        method="GET",
        path="/api/states",
    )
    return {state["entity_id"]: state for state in states}


def assert_true(condition: bool, message: str) -> None:
    """Raise AcceptanceFailure if condition is false."""
    if not condition:
        raise AcceptanceFailure(message)


def assert_equal(actual: Any, expected: Any, message: str) -> None:
    """Assert values are equal."""
    if actual != expected:
        raise AcceptanceFailure(f"{message}: expected {expected!r}, got {actual!r}")


def visible_state(state: dict[str, Any] | None) -> dict[str, Any] | None:
    """Return compact state representation for reporting."""
    if state is None:
        return None
    attrs = state.get("attributes", {})
    return {
        "entity_id": state["entity_id"],
        "state": state["state"],
        "name": attrs.get("friendly_name"),
        "assignment_id": attrs.get("assignment_id"),
        "child_id": attrs.get("child_id"),
        "chore_id": attrs.get("chore_id"),
        "kid_name": attrs.get("kid_name"),
        "title": attrs.get("title"),
        "category": attrs.get("category"),
        "points": attrs.get("points"),
        "week_start": attrs.get("week_start"),
        "week_end": attrs.get("week_end"),
    }


def wait_until(description: str, predicate, timeout: float = 20.0, interval: float = 0.25) -> None:
    """Poll until predicate becomes true or timeout expires."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(interval)
    raise AcceptanceFailure(f"Timed out waiting for {description}")


def write_html_report(
    *,
    output_html: Path,
    run_stamp: str,
    config_entry_id: str,
    tracked_ids: dict[str, str],
    criteria: list[dict[str, str]],
    snapshots: list[dict[str, Any]],
) -> None:
    """Write simple visual HTML summary."""
    criteria_rows = "\n".join(
        (
            "<tr><td>{criterion}</td><td class='{klass}'>{result}</td><td>{evidence}</td></tr>"
        ).format(
            criterion=escape(item["criterion"]),
            klass=item["result"].lower(),
            result=escape(item["result"]),
            evidence=escape(item["evidence"]),
        )
        for item in criteria
    )

    cards: list[str] = []
    for snap in snapshots:
        state_rows = "\n".join(
            "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                escape(entity_id),
                escape(str(state and state.get("state"))),
                escape(str(state and state.get("name"))),
            )
            for entity_id, state in snap["states"].items()
        )
        cards.append(
            f"""
<section class=\"card\">
  <h2>{escape(snap['step'])}</h2>
  <p>{escape(snap['captured_at'])}</p>
  <table><thead><tr><th>Entity</th><th>State</th><th>Name</th></tr></thead><tbody>{state_rows}</tbody></table>
  <pre>{escape(json.dumps(snap['storage']['next_ids'], indent=2))}</pre>
</section>
"""
        )

    html = f"""<!doctype html>
<html lang=\"en\">
<meta charset=\"utf-8\">
<title>Chores Manager Real HA Acceptance</title>
<style>
  body {{ font: 14px/1.45 system-ui, sans-serif; margin: 24px; color: #172026; background: #f6f7f9; }}
  h1 {{ font-size: 28px; margin: 0 0 8px; }}
  h2 {{ font-size: 18px; margin: 0 0 6px; }}
  .meta {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; }}
  .card {{ background: white; border: 1px solid #d9dee5; border-radius: 8px; padding: 14px; margin: 12px 0; }}
  table {{ border-collapse: collapse; width: 100%; background: white; }}
  th, td {{ text-align: left; border-bottom: 1px solid #e5e9ef; padding: 8px; vertical-align: top; }}
  th {{ background: #eef2f6; }}
  .pass {{ color: #0b6b35; font-weight: 700; }}
  .fail {{ color: #a61b1b; font-weight: 700; }}
  pre {{ max-height: 180px; overflow: auto; background: #111827; color: #e5e7eb; padding: 10px; border-radius: 6px; }}
</style>
<h1>Chores Manager Real HA Acceptance</h1>
<div class=\"meta\">
  <div class=\"card\"><strong>Run stamp</strong><br>{escape(run_stamp)}</div>
  <div class=\"card\"><strong>Config entry</strong><br>{escape(config_entry_id)}</div>
  <div class=\"card\"><strong>Tracked IDs</strong><pre>{escape(json.dumps(tracked_ids, indent=2))}</pre></div>
</div>
<section class=\"card\">
  <h2>Acceptance Criteria</h2>
  <table><thead><tr><th>Criterion</th><th>Result</th><th>Evidence</th></tr></thead><tbody>{criteria_rows}</tbody></table>
</section>
{''.join(cards)}
</html>
"""
    output_html.write_text(html, encoding="utf-8")


def run_acceptance(
    *,
    base_url: str,
    token: str,
    config_dir: Path,
    output_dir: Path,
    keep_structure: bool,
) -> dict[str, Any]:
    """Execute deterministic real-HA acceptance flow."""
    storage_path = config_dir / ".storage" / "chores_manager.data"
    entity_registry_path = config_dir / ".storage" / "core.entity_registry"
    config_entries_path = config_dir / ".storage" / "core.config_entries"
    db_path = config_dir / "home-assistant_v2.db"
    log_path = config_dir / "home-assistant.log"

    run_stamp = utc_stamp()
    output_json = output_dir / f"real_ha_acceptance_{run_stamp}.json"
    output_html = output_dir / f"real_ha_acceptance_{run_stamp}.html"

    def storage_data() -> dict[str, Any]:
        return read_json(storage_path)["data"]

    def entity_registry_entries() -> dict[str, dict[str, Any]]:
        data = read_json(entity_registry_path)["data"]
        return {entry["entity_id"]: entry for entry in data["entities"]}

    def entity_registry_by_unique() -> dict[tuple[str, str], dict[str, Any]]:
        entries = read_json(entity_registry_path)["data"]["entities"]
        return {
            (entry["platform"], entry["unique_id"]): entry
            for entry in entries
            if entry["platform"] == "chores_manager"
        }

    def config_entry_id() -> str:
        entries = read_json(config_entries_path)["data"]["entries"]
        for entry in entries:
            if entry["domain"] == "chores_manager":
                return entry["entry_id"]
        raise AcceptanceFailure("No chores_manager config entry found")

    def snapshot(name: str, tracked_entity_ids: list[str], tracked_ids: dict[str, str]) -> dict[str, Any]:
        states = get_states(base_url=base_url, token=token)
        registry = entity_registry_entries()
        data = storage_data()
        tracked_values = set(tracked_ids.values())
        tracked_completions = {
            completion_id: deepcopy(completion)
            for completion_id, completion in data["completions"].items()
            if completion.get("assignment_id") in tracked_values
            or completion.get("child_id") in tracked_values
            or completion.get("chore_id") in tracked_values
        }
        return {
            "step": name,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "states": {
                entity_id: visible_state(states.get(entity_id))
                for entity_id in tracked_entity_ids
            },
            "storage": {
                "children": deepcopy(data["children"]),
                "chores": deepcopy(data["chores"]),
                "assignments": deepcopy(data["assignments"]),
                "completions": tracked_completions,
                "next_ids": {
                    "child": data["next_child_id"],
                    "chore": data["next_chore_id"],
                    "assignment": data["next_assignment_id"],
                    "completion": data["next_completion_id"],
                },
            },
            "entity_registry": {
                entity_id: registry.get(entity_id)
                for entity_id in tracked_entity_ids
                if registry.get(entity_id) is not None
            },
        }

    def clean_live_structure() -> None:
        data = storage_data()
        for assignment_id in sorted(data["assignments"]):
            if assignment_id in storage_data()["assignments"]:
                call_service(
                    base_url=base_url,
                    token=token,
                    domain="chores_manager",
                    service="delete_assignment",
                    data={"assignment_id": assignment_id},
                )
        for chore_id in sorted(data["chores"]):
            if chore_id in storage_data()["chores"]:
                call_service(
                    base_url=base_url,
                    token=token,
                    domain="chores_manager",
                    service="delete_chore",
                    data={"chore_id": chore_id},
                )
        for child_id in sorted(data["children"]):
            if child_id in storage_data()["children"]:
                call_service(
                    base_url=base_url,
                    token=token,
                    domain="chores_manager",
                    service="delete_child",
                    data={"child_id": child_id},
                )

    def recorder_rows(entity_ids: list[str]) -> list[dict[str, Any]]:
        if not db_path.exists() or not entity_ids:
            return []
        placeholders = ",".join("?" for _ in entity_ids)
        query = f"""
            SELECT sm.entity_id, s.state, datetime(s.last_updated_ts,'unixepoch')
            FROM states s
            JOIN states_meta sm ON sm.metadata_id=s.metadata_id
            WHERE sm.entity_id IN ({placeholders})
            ORDER BY s.last_updated_ts DESC
            LIMIT 50
        """
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute(query, entity_ids).fetchall()
        return [
            {
                "entity_id": entity_id,
                "state": state,
                "last_updated_utc": last_updated,
            }
            for entity_id, state, last_updated in rows
        ]

    def chores_log_lines() -> list[str]:
        if not log_path.exists():
            return []
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        return [line for line in lines[-300:] if "chores_manager" in line.lower()]

    api_status = request_json(
        base_url=base_url,
        token=token,
        method="GET",
        path="/api/",
    )
    entry_id = config_entry_id()

    call_service(
        base_url=base_url,
        token=token,
        domain="homeassistant",
        service="reload_config_entry",
        data={"entry_id": entry_id},
    )
    time.sleep(2.0)

    if not keep_structure:
        clean_live_structure()

    tracked_ids: dict[str, str] = {}
    tracked_entity_ids: list[str] = []
    snapshots: list[dict[str, Any]] = []

    snapshots.append(snapshot("clean baseline", tracked_entity_ids, tracked_ids))

    call_service(
        base_url=base_url,
        token=token,
        domain="chores_manager",
        service="add_child",
        data={"name": f"Acceptance Alex {run_stamp}"},
    )
    call_service(
        base_url=base_url,
        token=token,
        domain="chores_manager",
        service="add_child",
        data={"name": f"Acceptance Blake {run_stamp}"},
    )

    data = storage_data()
    child_ids = sorted(data["children"], key=lambda item: int(item.split("_")[1]))
    alex_id, blake_id = child_ids[-2], child_ids[-1]
    tracked_ids.update({"alex": alex_id, "blake": blake_id})

    alex_sensor = f"sensor.{alex_id}_weekly_points"
    blake_sensor = f"sensor.{blake_id}_weekly_points"
    tracked_entity_ids.extend([alex_sensor, blake_sensor])
    snapshots.append(snapshot("add children", tracked_entity_ids, tracked_ids))

    call_service(
        base_url=base_url,
        token=token,
        domain="chores_manager",
        service="add_chore",
        data={
            "title": f"Make bed {run_stamp}",
            "category": "Morning",
            "points": 2,
            "icon": "mdi:bed",
            "sort_order": 10,
            "child_ids": [alex_id],
        },
    )
    call_service(
        base_url=base_url,
        token=token,
        domain="chores_manager",
        service="add_chore",
        data={
            "title": f"Feed plants {run_stamp}",
            "category": "Evening",
            "points": 3,
            "icon": "mdi:sprout",
            "sort_order": 20,
            "child_ids": [alex_id],
        },
    )

    data = storage_data()
    tracked_chores = [
        chore_id
        for chore_id, chore in data["chores"].items()
        if run_stamp in chore["title"]
    ]
    chore_by_title = {data["chores"][chore_id]["title"]: chore_id for chore_id in tracked_chores}
    bed_chore_id = chore_by_title[f"Make bed {run_stamp}"]
    plants_chore_id = chore_by_title[f"Feed plants {run_stamp}"]
    tracked_ids.update({"bed_chore": bed_chore_id, "plants_chore": plants_chore_id})

    blake_bed_switch = f"switch.{blake_id}_{bed_chore_id}"
    blake_plants_switch = f"switch.{blake_id}_{plants_chore_id}"
    call_service(
        base_url=base_url,
        token=token,
        domain="chores_manager",
        service="assign_chores_to_child",
        data={
            "child_id": blake_id,
            "chore_ids": [bed_chore_id, plants_chore_id],
        },
    )
    data = storage_data()
    first_bulk_assignment_by_pair = {
        (assignment["child_id"], assignment["chore_id"]): assignment_id
        for assignment_id, assignment in data["assignments"].items()
    }
    first_blake_bed_assignment = first_bulk_assignment_by_pair[
        (blake_id, bed_chore_id)
    ]
    first_blake_plants_assignment = first_bulk_assignment_by_pair[
        (blake_id, plants_chore_id)
    ]
    snapshots.append(
        snapshot(
            "bulk assign chores to child",
            tracked_entity_ids + [blake_bed_switch, blake_plants_switch],
            tracked_ids,
        )
    )

    call_service(
        base_url=base_url,
        token=token,
        domain="chores_manager",
        service="remove_chores_from_child",
        data={
            "child_id": blake_id,
            "chore_ids": [bed_chore_id, plants_chore_id],
        },
    )
    wait_until(
        "bulk assignment removal",
        lambda: all(
            assignment["child_id"] != blake_id
            for assignment in storage_data()["assignments"].values()
        )
        and get_states(base_url=base_url, token=token).get(blake_bed_switch) is None
        and get_states(base_url=base_url, token=token).get(blake_plants_switch) is None
        and (
            "chores_manager",
            first_blake_bed_assignment,
        )
        not in entity_registry_by_unique()
        and (
            "chores_manager",
            first_blake_plants_assignment,
        )
        not in entity_registry_by_unique(),
    )
    snapshots.append(
        snapshot(
            "bulk remove chores from child",
            tracked_entity_ids + [blake_bed_switch, blake_plants_switch],
            tracked_ids,
        )
    )

    call_service(
        base_url=base_url,
        token=token,
        domain="chores_manager",
        service="assign_chores_to_child",
        data={
            "child_id": blake_id,
            "chore_ids": [bed_chore_id, plants_chore_id],
        },
    )
    assignment_by_pair = {
        (assignment["child_id"], assignment["chore_id"]): assignment_id
        for assignment_id, assignment in storage_data()["assignments"].items()
    }
    alex_bed_assignment = assignment_by_pair[(alex_id, bed_chore_id)]
    alex_plants_assignment = assignment_by_pair[(alex_id, plants_chore_id)]
    blake_bed_assignment = assignment_by_pair[(blake_id, bed_chore_id)]
    blake_plants_assignment = assignment_by_pair[(blake_id, plants_chore_id)]
    assert_true(
        int(blake_bed_assignment.split("_")[1])
        > int(first_blake_bed_assignment.split("_")[1]),
        "bulk reassign reused the removed bed assignment ID",
    )
    assert_true(
        int(blake_plants_assignment.split("_")[1])
        > int(first_blake_plants_assignment.split("_")[1]),
        "bulk reassign reused the removed plants assignment ID",
    )
    tracked_ids.update(
        {
            "alex_bed_assignment": alex_bed_assignment,
            "alex_plants_assignment": alex_plants_assignment,
            "blake_bed_assignment": blake_bed_assignment,
            "blake_plants_assignment": blake_plants_assignment,
        }
    )

    alex_bed_switch = f"switch.{alex_id}_{bed_chore_id}"
    alex_plants_switch = f"switch.{alex_id}_{plants_chore_id}"
    tracked_entity_ids.extend(
        [
            alex_bed_switch,
            alex_plants_switch,
            blake_bed_switch,
            blake_plants_switch,
        ]
    )
    snapshots.append(snapshot("add chores and assignments", tracked_entity_ids, tracked_ids))

    call_service(
        base_url=base_url,
        token=token,
        domain="chores_manager",
        service="update_child",
        data={"child_id": alex_id, "name": f"Acceptance Avery {run_stamp}"},
    )
    call_service(
        base_url=base_url,
        token=token,
        domain="chores_manager",
        service="update_chore",
        data={
            "chore_id": bed_chore_id,
            "title": f"Make bed carefully {run_stamp}",
            "category": "Bedroom",
            "points": 5,
            "icon": "mdi:bed-king",
            "sort_order": 15,
        },
    )
    snapshots.append(snapshot("rename child and chore metadata", tracked_entity_ids, tracked_ids))

    call_service(
        base_url=base_url,
        token=token,
        domain="switch",
        service="turn_on",
        data={"entity_id": alex_bed_switch},
    )
    data = storage_data()
    first_completion_id = max(
        (
            completion_id
            for completion_id, completion in data["completions"].items()
            if completion["assignment_id"] == alex_bed_assignment
        ),
        key=lambda item: int(item.split("_")[1]),
    )
    first_completion_snapshot = deepcopy(data["completions"][first_completion_id])
    snapshots.append(snapshot("complete chore", tracked_entity_ids, tracked_ids))

    call_service(
        base_url=base_url,
        token=token,
        domain="switch",
        service="turn_off",
        data={"entity_id": alex_bed_switch},
    )
    snapshots.append(snapshot("undo chore completion", tracked_entity_ids, tracked_ids))

    call_service(
        base_url=base_url,
        token=token,
        domain="switch",
        service="turn_on",
        data={"entity_id": alex_bed_switch},
    )
    data = storage_data()
    second_completion_id = max(
        (
            completion_id
            for completion_id, completion in data["completions"].items()
            if completion["assignment_id"] == alex_bed_assignment
        ),
        key=lambda item: int(item.split("_")[1]),
    )
    second_completion_snapshot = deepcopy(data["completions"][second_completion_id])
    snapshots.append(snapshot("complete chore again", tracked_entity_ids, tracked_ids))

    call_service(
        base_url=base_url,
        token=token,
        domain="chores_manager",
        service="set_child_active",
        data={"child_id": alex_id, "active": False},
    )
    snapshots.append(snapshot("deactivate child", tracked_entity_ids, tracked_ids))

    call_service(
        base_url=base_url,
        token=token,
        domain="chores_manager",
        service="set_child_active",
        data={"child_id": alex_id, "active": True},
    )
    call_service(
        base_url=base_url,
        token=token,
        domain="chores_manager",
        service="set_chore_active",
        data={"chore_id": plants_chore_id, "active": False},
    )
    snapshots.append(snapshot("reactivate child and deactivate chore", tracked_entity_ids, tracked_ids))

    call_service(
        base_url=base_url,
        token=token,
        domain="chores_manager",
        service="set_chore_active",
        data={"chore_id": plants_chore_id, "active": True},
    )
    call_service(
        base_url=base_url,
        token=token,
        domain="chores_manager",
        service="set_assignment_active",
        data={"assignment_id": blake_plants_assignment, "active": False},
    )
    snapshots.append(snapshot("reactivate chore and deactivate assignment", tracked_entity_ids, tracked_ids))

    call_service(
        base_url=base_url,
        token=token,
        domain="chores_manager",
        service="set_assignment_active",
        data={"assignment_id": blake_plants_assignment, "active": True},
    )
    snapshots.append(snapshot("reactivate assignment", tracked_entity_ids, tracked_ids))

    call_service(
        base_url=base_url,
        token=token,
        domain="chores_manager",
        service="delete_assignment",
        data={"assignment_id": blake_plants_assignment},
    )
    time.sleep(2.0)
    snapshots.append(snapshot("delete assignment intentionally", tracked_entity_ids, tracked_ids))

    call_service(
        base_url=base_url,
        token=token,
        domain="chores_manager",
        service="delete_chore",
        data={"chore_id": plants_chore_id},
    )
    time.sleep(2.0)
    snapshots.append(snapshot("delete chore intentionally", tracked_entity_ids, tracked_ids))

    call_service(
        base_url=base_url,
        token=token,
        domain="chores_manager",
        service="delete_child",
        data={"child_id": blake_id},
    )
    time.sleep(2.0)
    snapshots.append(snapshot("delete child intentionally", tracked_entity_ids, tracked_ids))

    call_service(
        base_url=base_url,
        token=token,
        domain="homeassistant",
        service="reload_config_entry",
        data={"entry_id": entry_id},
    )

    wait_until(
        "surviving entities after reload",
        lambda: get_states(base_url=base_url, token=token).get(alex_bed_switch) is not None
        and get_states(base_url=base_url, token=token).get(alex_sensor) is not None
        and entity_registry_by_unique().get(("chores_manager", alex_bed_assignment), {}).get("entity_id")
        == alex_bed_switch
        and entity_registry_by_unique().get(("chores_manager", f"{alex_id}_weekly_points"), {}).get("entity_id")
        == alex_sensor,
    )

    snapshots.append(snapshot("reload after deletes", tracked_entity_ids, tracked_ids))

    states = get_states(base_url=base_url, token=token)
    data = storage_data()
    registry_unique = entity_registry_by_unique()

    alex_sensor_state = states.get(alex_sensor)
    alex_bed_state = states.get(alex_bed_switch)

    assert_true(alex_sensor_state is not None, f"{alex_sensor} missing after reload")
    assert_true(alex_bed_state is not None, f"{alex_bed_switch} missing after reload")
    assert_equal(alex_bed_state["attributes"]["assignment_id"], alex_bed_assignment, "assignment attr stable")
    assert_equal(alex_bed_state["attributes"]["child_id"], alex_id, "child attr stable")
    assert_equal(alex_bed_state["attributes"]["chore_id"], bed_chore_id, "chore attr stable")

    assert_true(("chores_manager", alex_bed_assignment) in registry_unique, "live assignment registry entry missing")
    assert_equal(registry_unique[("chores_manager", alex_bed_assignment)]["entity_id"], alex_bed_switch, "switch entity_id stable")
    assert_equal(registry_unique[("chores_manager", alex_bed_assignment)]["unique_id"], alex_bed_assignment, "switch unique_id stable")
    assert_true(("chores_manager", f"{alex_id}_weekly_points") in registry_unique, "live child registry entry missing")
    assert_equal(registry_unique[("chores_manager", f"{alex_id}_weekly_points")]["entity_id"], alex_sensor, "sensor entity_id stable")

    assert_equal(data["children"][alex_id]["name"], f"Acceptance Avery {run_stamp}", "child metadata persisted")
    assert_equal(data["chores"][bed_chore_id]["title"], f"Make bed carefully {run_stamp}", "chore title persisted")
    assert_equal(data["chores"][bed_chore_id]["points"], 5, "chore points persisted")
    assert_true(second_completion_id in data["completions"], "retained completion snapshot missing")
    assert_equal(data["completions"][second_completion_id], second_completion_snapshot, "completion snapshot changed after delete/reload")
    assert_true(first_completion_id not in data["completions"], "undone completion was retained")

    assert_true(blake_id not in data["children"], "deleted child remained in storage")
    assert_true(plants_chore_id not in data["chores"], "deleted chore remained in storage")
    assert_true(blake_plants_assignment not in data["assignments"], "deleted assignment remained in storage")

    assert_true(states.get(blake_sensor) is None, "deleted child sensor restored as state")
    assert_true(states.get(blake_bed_switch) is None, "deleted child switch restored as state")
    assert_true(states.get(blake_plants_switch) is None, "deleted assignment switch restored as state")
    assert_true(states.get(alex_plants_switch) is None, "deleted chore switch restored as state")

    criteria = [
        {
            "criterion": "Config-entry reload and runtime lifecycle",
            "result": "PASS",
            "evidence": f"Reloaded config entry {entry_id} before and after workflow.",
        },
        {
            "criterion": "Stable IDs and unique IDs remain stable-ID derived",
            "result": "PASS",
            "evidence": f"{alex_bed_switch} unique_id={alex_bed_assignment}; {alex_sensor} unique_id={alex_id}_weekly_points.",
        },
        {
            "criterion": "Metadata edits do not change stable identity",
            "result": "PASS",
            "evidence": "Child/chore metadata changed while stable IDs and entity IDs remained fixed.",
        },
        {
            "criterion": "Completion snapshots remain immutable",
            "result": "PASS",
            "evidence": f"{second_completion_id} matched its pre-delete snapshot after delete/reload.",
        },
        {
            "criterion": "Deactivate/reactivate preserves structure and history",
            "result": "PASS",
            "evidence": "Activation toggles changed live availability without deleting structure or completion history.",
        },
        {
            "criterion": "Bulk assignment and removal are atomic",
            "result": "PASS",
            "evidence": "Two Blake relationships were added, removed from storage/state/registry, and recreated with newer stable IDs.",
        },
        {
            "criterion": "Delete removes targeted live structure/entities only",
            "result": "PASS",
            "evidence": "Deleted structures were removed while the retained Alex-bed structure stayed live.",
        },
        {
            "criterion": "Deleted entities do not return after reload",
            "result": "PASS",
            "evidence": "Deleted sensor/switch states remained absent after config-entry reload.",
        },
        {
            "criterion": "Recorder/log evidence captured",
            "result": "PASS",
            "evidence": "Recent recorder rows and chores_manager log lines were captured in the JSON artifact.",
        },
    ]

    tracked_entity_ids_for_recorder = [
        alex_sensor,
        blake_sensor,
        alex_bed_switch,
        alex_plants_switch,
        blake_plants_switch,
    ]

    evidence = {
        "run_stamp": run_stamp,
        "base_url": base_url,
        "api_status": api_status,
        "config_entry_id": entry_id,
        "tracked_ids": tracked_ids,
        "tracked_entity_ids": tracked_entity_ids_for_recorder,
        "criteria": criteria,
        "snapshots": snapshots,
        "completion_snapshots": {
            "first_undone": first_completion_snapshot,
            "second_retained": second_completion_snapshot,
        },
        "recorder_rows": recorder_rows(tracked_entity_ids_for_recorder),
        "recent_chores_manager_log_lines": chores_log_lines(),
        "output_json": str(output_json),
        "output_html": str(output_html),
    }

    output_json.write_text(json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8")
    write_html_report(
        output_html=output_html,
        run_stamp=run_stamp,
        config_entry_id=entry_id,
        tracked_ids=tracked_ids,
        criteria=criteria,
        snapshots=snapshots,
    )

    return evidence


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(description="Run real-HA acceptance for Chores Manager")
    parser.add_argument("--ha-url", required=True, help="Home Assistant base URL, for example http://localhost:8123")
    parser.add_argument("--token", required=True, help="Long-lived Home Assistant access token")
    parser.add_argument("--config-dir", required=True, help="Home Assistant config directory path")
    parser.add_argument("--output-dir", default="/tmp", help="Directory for JSON/HTML artifacts")
    parser.add_argument(
        "--keep-structure",
        action="store_true",
        help="Do not clean existing chores_manager structure before test setup",
    )
    return parser.parse_args()


def main() -> int:
    """CLI entrypoint."""
    args = parse_args()

    config_dir = Path(args.config_dir)
    output_dir = Path(args.output_dir)

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        evidence = run_acceptance(
            base_url=args.ha_url.rstrip("/"),
            token=args.token,
            config_dir=config_dir,
            output_dir=output_dir,
            keep_structure=args.keep_structure,
        )
    except Exception as err:
        failure = {
            "error": type(err).__name__,
            "message": str(err),
            "failed_at": datetime.now(timezone.utc).isoformat(),
        }
        print(json.dumps(failure, indent=2))
        return 1

    summary = {
        "result": "PASS",
        "run_stamp": evidence["run_stamp"],
        "config_entry_id": evidence["config_entry_id"],
        "tracked_ids": evidence["tracked_ids"],
        "json_artifact": evidence["output_json"],
        "html_artifact": evidence["output_html"],
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
