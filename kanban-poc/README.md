# Kanban POC


```bash
# Kanban CLI – Full Test Command List (Current Version)

# Reset state
rm -f kanban.json


# 1. Create sprint
python kanban.py sprint add \\
  --code S-1 \\
  --name "Core Auth Sprint" \\
  --start-date 2025-12-01 \\
  --end-date 2025-12-15

python kanban.py sprint list


# 2. Create tasks
python kanban.py add \\
  --code T-1 \\
  --name "Login endpoint" \\
  --status TODO

python kanban.py add \\
  --code T-2 \\
  --name "Password hashing" \\
  --status TODO \\
  --sprint S-1 \\
  --estimate 1.5h

python kanban.py add \\
  --code T-3 \\
  --name "JWT middleware" \\
  --status IN_PROGRESS \\
  --start-date 2025-12-02 \\
  --review-date 2025-12-05


# 3. List tasks
python kanban.py list
python kanban.py list --status TODO
python kanban.py list --sprint S-1


# 4. Board views
python kanban.py board
python kanban.py board --sprint S-1
python kanban.py board --current


# 5. Move tasks
python kanban.py move T-2 IN_PROGRESS
python kanban.py move T-2 REVIEW
python kanban.py move T-2 DONE

python kanban.py board --current


# 6. Add / edit comment (opens vi, multiline)
python kanban.py task comment T-3


# 7. Show task details
python kanban.py task show T-3


# 8. Edit task (single command – flags)
python kanban.py task edit T-3 \\
  --name "JWT auth middleware" \\
  --status REVIEW \\
  --estimate 2h \\
  --actual 2.5h \\
  --end-date 2025-12-10

python kanban.py task show T-3


# 9. Edit task (ALL fields via vi)
python kanban.py task vi T-3


# 10. Close sprint
python kanban.py sprint close S-1
python kanban.py sprint list


# 11. Board after sprint close
python kanban.py board --current


# 12. Error handling checks
python kanban.py move T-999 DONE
python kanban.py task show T-999
python kanban.py board --sprint S-999
python kanban.py sprint close S-999


# 13. Inspect storage
cat kanban.json
```
