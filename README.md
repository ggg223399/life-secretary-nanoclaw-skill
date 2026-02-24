# life-secretary-nanoclaw-skill

Nanoclaw setup skill for deploying Life Secretary into a dedicated group folder.

## Install

```bash
cd .claude/skills
git clone https://github.com/ggg223399/life-secretary-nanoclaw-skill life-secretary
```

## Usage

1. Open Claude Code in your VPS workspace.
2. Run `/life-secretary`.
3. Follow guided setup prompts:
   - group folder name
   - Telegram ready or not
   - optional chat ID registration

The setup skill deploys the operational agent into your target group under `.claude/skills/life-secretary/`.

## Update

```bash
cd .claude/skills/life-secretary
git pull
```

Then run `/life-secretary` again to redeploy files if needed.

## Operational Tools (16)

1. `view_schedule`
2. `add_event`
3. `delete_event`
4. `detect_conflicts`
5. `manage_anchor`
6. `protect_focus`
7. `manage_flex_block`
8. `set_degradation`
9. `log_body_status`
10. `view_habits`
11. `weekly_review`
12. `manage_tasks`
13. `schedule_task`
14. `estimate_task_time`
15. `optimize_day`
16. `planner_settings`

## Repository Structure

```text
life-secretary-nanoclaw-skill/
├── SKILL.md
├── agent/
│   ├── SKILL.md
│   ├── CLAUDE.md
│   ├── schema.sql
│   ├── init-db.sh
│   └── plans/
│       └── fitness-plan.md
└── README.md
```

- Root `SKILL.md`: setup/deployment workflow (phase-based)
- `agent/SKILL.md`: operational Life Secretary skill used at runtime
- `agent/CLAUDE.md`: group-level trigger and routing guidance
- `agent/schema.sql` + `agent/init-db.sh`: SQLite initialization assets
- `agent/plans/fitness-plan.md`: built-in fitness reference plan

## Notes

- `github_push_files` adds/updates files in one commit.
- Legacy root files (`CLAUDE.md`, `schema.sql`, `init-db.sh`, `plans/fitness-plan.md`) may remain until a follow-up cleanup commit.

## License

MIT
