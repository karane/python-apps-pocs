#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import tempfile
from datetime import datetime

DATA_FILE = "kanban.json"

STATUS_ORDER = [
    "TODO",
    "IN_PROGRESS",
    "REVIEW",
    "TESTING_DEPLOYMENT",
    "DONE",
]

STATUSES = set(STATUS_ORDER)

# =========================
# Storage
# =========================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "sprints": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# =========================
# Validation
# =========================

def validate_status(status):
    if status not in STATUSES:
        print(f"Invalid status. Valid: {', '.join(STATUS_ORDER)}")
        return False
    return True


def validate_date(date_str):
    if date_str is None:
        return True
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        print(f"Invalid date format: {date_str} (expected YYYY-MM-DD)")
        return False


def validate_time_value(value):
    if value is None:
        return True
    if not isinstance(value, str):
        print("Time must be a string like 1h, 30m, 1.5h")
        return False
    return True


def get_open_sprints(data):
    return [s for s in data["sprints"].values() if not s["closed"]]


# =========================
# Tasks
# =========================

def add_task(args):
    data = load_data()

    if args.code in data["tasks"]:
        print("Task already exists")
        return

    if not validate_status(args.status):
        return

    if not validate_time_value(args.estimate):
        return

    for d in [args.start_date, args.review_date, args.end_date]:
        if not validate_date(d):
            return

    if args.sprint:
        sprint = data["sprints"].get(args.sprint)
        if not sprint:
            print("Sprint not found")
            return
        if sprint["closed"]:
            print("Sprint is closed")
            return

    data["tasks"][args.code] = {
        "code": args.code,
        "name": args.name,
        "start_date": args.start_date,
        "review_date": args.review_date,
        "end_date": args.end_date,
        "status": args.status,
        "sprint_code": args.sprint,
        "comment": None,
        "estimated_time": args.estimate,
        "actual_time": None,
    }

    save_data(data)
    print(f"Task '{args.code}' created")


def list_tasks(args):
    data = load_data()
    tasks = list(data["tasks"].values())

    if args.status:
        if not validate_status(args.status):
            return
        tasks = [t for t in tasks if t["status"] == args.status]

    if args.sprint:
        if args.sprint not in data["sprints"]:
            print("Sprint not found")
            return
        tasks = [t for t in tasks if t["sprint_code"] == args.sprint]

    if not tasks:
        print("No tasks found")
        return

    for t in tasks:
        sprint = t["sprint_code"] or "-"
        mark = "💬" if t.get("comment") else ""
        print(f"[{t['status']}] {t['code']} - {t['name']} {mark} (sprint: {sprint})")


def move_task(args):
    data = load_data()
    task = data["tasks"].get(args.code)

    if not task:
        print("Task not found")
        return

    if not validate_status(args.status):
        return

    old = task["status"]
    task["status"] = args.status
    save_data(data)

    print(f"Task '{args.code}' moved: {old} → {args.status}")


def task_edit(args):
    data = load_data()
    task = data["tasks"].get(args.code)

    if not task:
        print("Task not found")
        return

    updated = False

    if args.name:
        task["name"] = args.name
        updated = True

    if args.status:
        if not validate_status(args.status):
            return
        task["status"] = args.status
        updated = True

    if args.estimate is not None:
        if not validate_time_value(args.estimate):
            return
        task["estimated_time"] = args.estimate
        updated = True

    if args.actual is not None:
        if not validate_time_value(args.actual):
            return
        task["actual_time"] = args.actual
        updated = True

    if args.start_date is not None:
        if not validate_date(args.start_date):
            return
        task["start_date"] = args.start_date
        updated = True

    if args.review_date is not None:
        if not validate_date(args.review_date):
            return
        task["review_date"] = args.review_date
        updated = True

    if args.end_date is not None:
        if not validate_date(args.end_date):
            return
        task["end_date"] = args.end_date
        updated = True

    if not updated:
        print("No changes provided")
        return

    save_data(data)
    print(f"Task '{args.code}' updated")


# =========================
# Board
# =========================

def board_tasks(args):
    data = load_data()
    tasks = list(data["tasks"].values())
    sprint = None

    if args.current:
        open_sprints = get_open_sprints(data)
        if not open_sprints:
            print("No active sprint found")
            return
        if len(open_sprints) > 1:
            print("More than one active sprint found")
            return
        sprint = open_sprints[0]
        tasks = [t for t in tasks if t["sprint_code"] == sprint["code"]]

    elif args.sprint:
        sprint = data["sprints"].get(args.sprint)
        if not sprint:
            print("Sprint not found")
            return
        tasks = [t for t in tasks if t["sprint_code"] == args.sprint]

    grouped = {s: [] for s in STATUS_ORDER}
    for t in tasks:
        grouped[t["status"]].append(t)

    title = "KANBAN BOARD"
    if sprint:
        title += f" — {sprint['code']} ({sprint['name']})"

    print(title)
    print("=" * len(title))
    print()

    for status in STATUS_ORDER:
        print(status)
        print("-" * len(status))
        if not grouped[status]:
            print("(no tasks)")
        else:
            for t in grouped[status]:
                mark = "💬" if t.get("comment") else ""
                print(f"{t['code']}  {t['name']} {mark}")
        print()


# =========================
# Task Edit via VI (ALL FIELDS)
# =========================

def task_edit_vi(args):
    data = load_data()
    task = data["tasks"].get(args.code)

    if not task:
        print("Task not found")
        return

    editor = os.environ.get("EDITOR", "vi")

    template = f"""# Edit task fields below
# Lines starting with # are ignored
# Leave a value empty to keep current value
# ----------------------------

name={task['name']}
status={task['status']}
sprint={task['sprint_code'] or ''}
start_date={task['start_date'] or ''}
review_date={task['review_date'] or ''}
end_date={task['end_date'] or ''}
estimated_time={task['estimated_time'] or ''}
actual_time={task['actual_time'] or ''}

---COMMENT---
{task['comment'] or ''}
"""

    with tempfile.NamedTemporaryFile(delete=False, mode="w") as tf:
        path = tf.name
        tf.write(template)

    subprocess.call([editor, path])

    with open(path) as f:
        lines = f.readlines()

    os.unlink(path)

    updates = {}
    comment_lines = []
    in_comment = False

    for line in lines:
        line = line.rstrip("\n")

        if line == "---COMMENT---":
            in_comment = True
            continue

        if in_comment:
            comment_lines.append(line)
            continue

        if not line or line.startswith("#") or "=" not in line:
            continue

        k, v = line.split("=", 1)
        updates[k] = v.strip() or None

    if updates.get("status") and not validate_status(updates["status"]):
        return

    for d in ["start_date", "review_date", "end_date"]:
        if updates.get(d) and not validate_date(updates[d]):
            return

    for t in ["estimated_time", "actual_time"]:
        if updates.get(t) and not validate_time_value(updates[t]):
            return

    if updates.get("sprint"):
        sprint = data["sprints"].get(updates["sprint"])
        if not sprint:
            print("Sprint not found")
            return
        if sprint["closed"]:
            print("Sprint is closed")
            return

    for k, v in updates.items():
        if k == "sprint":
            task["sprint_code"] = v
        elif k in task:
            task[k] = v

    comment = "\n".join(comment_lines).rstrip()
    task["comment"] = comment if comment.strip() else None

    save_data(data)
    print(f"Task '{args.code}' updated via editor")


# =========================
# Task Comments
# =========================

def edit_task_comment(args):
    data = load_data()
    task = data["tasks"].get(args.code)

    if not task:
        print("Task not found")
        return

    editor = os.environ.get("EDITOR", "vi")

    with tempfile.NamedTemporaryFile(delete=False, mode="w") as tf:
        path = tf.name
        if task.get("comment"):
            tf.write(task["comment"])

    subprocess.call([editor, path])

    with open(path) as f:
        content = f.read().rstrip("\n")

    os.unlink(path)

    task["comment"] = content if content.strip() else None
    save_data(data)

    print(f"Comment updated for task '{args.code}'")


def task_show(args):
    data = load_data()
    task = data["tasks"].get(args.code)

    if not task:
        print("Task not found")
        return

    print(f"Task:        {task['code']}")
    print(f"Name:        {task['name']}")
    print(f"Status:      {task['status']}")
    print(f"Sprint:      {task['sprint_code'] or '-'}")
    print(f"Start date:  {task['start_date'] or '-'}")
    print(f"Review date: {task['review_date'] or '-'}")
    print(f"End date:    {task['end_date'] or '-'}")
    print(f"Estimate:    {task['estimated_time'] or '-'}")
    print(f"Actual:      {task['actual_time'] or '-'}")
    print("-" * 40)
    print("Comment:\n")
    print(task["comment"] if task["comment"] else "(no comment)")


# =========================
# Sprints
# =========================

def sprint_add(args):
    data = load_data()

    if args.code in data["sprints"]:
        print("Sprint already exists")
        return

    data["sprints"][args.code] = {
        "code": args.code,
        "name": args.name,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "closed": False,
    }

    save_data(data)
    print(f"Sprint '{args.code}' created")


def sprint_list(_):
    data = load_data()

    if not data["sprints"]:
        print("No sprints found")
        return

    for s in data["sprints"].values():
        state = "CLOSED" if s["closed"] else "OPEN"
        print(f"{s['code']} - {s['name']} ({s['start_date']} → {s['end_date']}) [{state}]")


def sprint_close(args):
    data = load_data()
    sprint = data["sprints"].get(args.code)

    if not sprint:
        print("Sprint not found")
        return

    if sprint["closed"]:
        print("Sprint already closed")
        return

    moved = 0
    for t in data["tasks"].values():
        if t["sprint_code"] == args.code and t["status"] != "DONE":
            t["sprint_code"] = None
            moved += 1

    sprint["closed"] = True
    save_data(data)

    print(f"Sprint '{args.code}' closed")
    print(f"{moved} unfinished tasks moved back to backlog")


# =========================
# CLI
# =========================

def main():
    parser = argparse.ArgumentParser(description="Kanban CLI")
    sub = parser.add_subparsers(required=True)

    add = sub.add_parser("add")
    add.add_argument("--code", required=True)
    add.add_argument("--name", required=True)
    add.add_argument("--status", required=True)
    add.add_argument("--sprint")
    add.add_argument("--estimate")
    add.add_argument("--start-date")
    add.add_argument("--review-date")
    add.add_argument("--end-date")
    add.set_defaults(func=add_task)

    lst = sub.add_parser("list")
    lst.add_argument("--status")
    lst.add_argument("--sprint")
    lst.set_defaults(func=list_tasks)

    mv = sub.add_parser("move")
    mv.add_argument("code")
    mv.add_argument("status")
    mv.set_defaults(func=move_task)

    brd = sub.add_parser("board")
    brd.add_argument("--sprint")
    brd.add_argument("--current", action="store_true")
    brd.set_defaults(func=board_tasks)

    task = sub.add_parser("task")
    task_sub = task.add_subparsers(required=True)

    te = task_sub.add_parser("edit")
    te.add_argument("code")
    te.add_argument("--name")
    te.add_argument("--status")
    te.add_argument("--estimate")
    te.add_argument("--actual")
    te.add_argument("--start-date")
    te.add_argument("--review-date")
    te.add_argument("--end-date")
    te.set_defaults(func=task_edit)

    tv = task_sub.add_parser("vi")
    tv.add_argument("code")
    tv.set_defaults(func=task_edit_vi)

    tc = task_sub.add_parser("comment")
    tc.add_argument("code")
    tc.set_defaults(func=edit_task_comment)

    ts = task_sub.add_parser("show")
    ts.add_argument("code")
    ts.set_defaults(func=task_show)

    sprint = sub.add_parser("sprint")
    sprint_sub = sprint.add_subparsers(required=True)

    s_add = sprint_sub.add_parser("add")
    s_add.add_argument("--code", required=True)
    s_add.add_argument("--name", required=True)
    s_add.add_argument("--start-date", required=True)
    s_add.add_argument("--end-date", required=True)
    s_add.set_defaults(func=sprint_add)

    s_list = sprint_sub.add_parser("list")
    s_list.set_defaults(func=sprint_list)

    s_close = sprint_sub.add_parser("close")
    s_close.add_argument("code")
    s_close.set_defaults(func=sprint_close)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
