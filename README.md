# life-secretary

Nanoclaw skill for life scheduling — SQLite-backed, pure instruction-based, no Node.js dependencies.

## Install

```bash
cd ~/.claude/skills/
git clone https://github.com/ggg223399/life-secretary-nanoclaw-skill life-secretary
```

## Update

```bash
cd ~/.claude/skills/life-secretary
git pull
```

## Setup

Append to nanoclaw CLAUDE.md:

```bash
cat CLAUDE.md >> ~/nanoclaw/CLAUDE.md
```

Initialize database (first time):

```bash
bash init-db.sh /workspace/group/life-secretary.db
```

## 16 Tools

- **Schedule**: view_schedule, add_event, delete_event, detect_conflicts
- **Anchors**: manage_anchor, protect_focus, manage_flex_block, set_degradation
- **Habits**: log_body_status, view_habits, weekly_review
- **Tasks**: manage_tasks, schedule_task, estimate_task_time, optimize_day, planner_settings

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Main skill instructions (274 lines) |
| `CLAUDE.md` | Nanoclaw integration snippet |
| `schema.sql` | SQLite schema (6 tables) |
| `init-db.sh` | Database initializer script |
| `plans/fitness-plan.md` | Sample fitness plan (681 lines) |

## Permissions

If `init-db.sh` is not executable after clone:

```bash
chmod +x init-db.sh
```

---

**License**: MIT
