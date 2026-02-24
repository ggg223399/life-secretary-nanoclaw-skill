# life-secretary-nanoclaw-skill

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

**1. Append to nanoclaw CLAUDE.md:**
```bash
cat ~/.claude/skills/life-secretary/CLAUDE.md >> ~/nanoclaw/CLAUDE.md
```

**2. Initialize database (first time only):**
```bash
# Run inside nanoclaw container, or let the skill auto-init on first use
bash init-db.sh /workspace/group/life-secretary.db
```

> Note: `init-db.sh` requires `sqlite3` CLI. If not available:
> `apt-get update && apt-get install -y sqlite3`

## 16 Tools

- **Schedule**: `view_schedule`, `add_event`, `delete_event`, `detect_conflicts`
- **Anchors**: `manage_anchor`, `protect_focus`, `manage_flex_block`, `set_degradation`
- **Health**: `log_body_status`, `view_habits`, `weekly_review`
- **Tasks**: `manage_tasks`, `schedule_task`, `estimate_task_time`, `optimize_day`, `planner_settings`

See `SKILL.md` for full operation guides.

## Files

| File | Description |
|------|-------------|
| `SKILL.md` | Core skill — 16 tools, schema, auto-init, built-in tests |
| `CLAUDE.md` | Guidance snippet to append to nanoclaw's CLAUDE.md |
| `schema.sql` | SQLite schema (6 tables, no Lark) |
| `init-db.sh` | DB initialization script |
| `plans/fitness-plan.md` | Personalized fitness plan |

## Data

SQLite DB stored at `/workspace/group/life-secretary.db` — persists via nanoclaw's mounted group directory.
