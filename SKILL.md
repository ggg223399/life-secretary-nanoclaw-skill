---
name: init-life-secretary
description: Deploy Life Secretary — personal schedule manager with SQLite storage, 16 management tools, habit tracking, and work-life balance. Creates a dedicated group with Telegram channel support.
---

# life-secretary

Deploy Life Secretary into a Nanoclaw group with guided setup.

## Phase 1: Pre-flight

1. Check `.nanoclaw/state.yaml`.
2. If `applied_skills` already includes `life-secretary`, ask whether to redeploy.

AskUserQuestion: "`life-secretary` is already deployed. Do you want to redeploy and overwrite skill files? (yes/no)"

- If user says `no`, stop.
- If user says `yes`, continue.

AskUserQuestion: "What should the group folder be named? (default: `life-secretary`)"

- Use user input as `{folder}`.
- If empty, set `{folder}=life-secretary`.

AskUserQuestion: "Do you already have a Telegram channel set up for this group? (yes/no)"

- If `yes`:
  AskUserQuestion: "Please provide the Telegram chat ID (example: `-1001234567890`). Hint: send `/chatid` to the bot in that chat to get it."
  Save as `{chat_id}`.
- If `no`:
  Mark `telegram_needed=true`.

> 中文提示：预检阶段只做确认，不改动文件。

## Phase 2: Create Group

Create directories:

```bash
mkdir -p "groups/{folder}/.claude/skills/life-secretary/plans"
```

Copy skill files from this repository's `agent/` directory:

```bash
cp "agent/SKILL.md" "groups/{folder}/.claude/skills/life-secretary/SKILL.md"
cp "agent/schema.sql" "groups/{folder}/.claude/skills/life-secretary/schema.sql"
cp "agent/init-db.sh" "groups/{folder}/.claude/skills/life-secretary/init-db.sh"
cp "agent/plans/fitness-plan.md" "groups/{folder}/.claude/skills/life-secretary/plans/fitness-plan.md"
cp "agent/sqlite3" "groups/{folder}/.claude/skills/life-secretary/sqlite3"
chmod +x "groups/{folder}/.claude/skills/life-secretary/sqlite3"
```

Handle `CLAUDE.md`:

- If `groups/{folder}/CLAUDE.md` does not exist:

```bash
cp "agent/CLAUDE.md" "groups/{folder}/CLAUDE.md"
```

- If it exists, append agent guidance:

```bash
printf "\n\n" >> "groups/{folder}/CLAUDE.md"
cat "agent/CLAUDE.md" >> "groups/{folder}/CLAUDE.md"
```

Make init script executable:

```bash
chmod +x "groups/{folder}/.claude/skills/life-secretary/init-db.sh"
```

## Phase 3: Channel Setup

If user already has Telegram (`{chat_id}` provided), register group:

```typescript
registerGroup("tg:{chat-id}", {
  name: "{folder}",
  folder: "{folder}",
  trigger: "@{ASSISTANT_NAME}",
  added_at: new Date().toISOString(),
  requiresTrigger: true,
});
```

If `telegram_needed=true`, tell user:

"After deployment is complete, run `/add-telegram` and point it at this group folder: `{folder}`"

> 中文提示：未配置 Telegram 也可先本地测试技能。

## Phase 4: Initialize Database

- Operational skill auto-initializes DB on first user message.
- Optional host check:

No manual DB action is required during deployment. The bundled Python sqlite3 wrapper is used automatically.

## Phase 5: Record & Verify

Update `.nanoclaw/state.yaml`:

```yaml
applied_skills:
  - life-secretary
life_secretary:
  folder: "{folder}"
  deployed_at: "{ISO timestamp}"
```

Verification checklist:

- [ ] `groups/{folder}/CLAUDE.md` exists and contains life-secretary section
- [ ] `groups/{folder}/.claude/skills/life-secretary/SKILL.md` exists
- [ ] `groups/{folder}/.claude/skills/life-secretary/schema.sql` exists
- [ ] `groups/{folder}/.claude/skills/life-secretary/init-db.sh` exists and is executable
- [ ] `groups/{folder}/.claude/skills/life-secretary/sqlite3` exists and is executable
- [ ] `groups/{folder}/.claude/skills/life-secretary/plans/fitness-plan.md` exists

Final message to user:

"Life Secretary deployed to `groups/{folder}/`. Send a message to your Telegram chat (or test locally) with: `看看今天日程`"

## Troubleshooting

- If agent says `sqlite3 not found`: the bundled Python wrapper should be used automatically; ensure `agent/sqlite3` was copied during deployment.
- If DB is not initialized, run inside container:

```bash
bash /workspace/group/.claude/skills/life-secretary/init-db.sh
```

- To update deployed files:

```bash
cd .claude/skills/life-secretary && git pull
```

Then re-run `/life-secretary` to redeploy.

## Update

```bash
cd .claude/skills/life-secretary && git pull
```

Re-run `/life-secretary`; it detects existing deployment and asks whether to redeploy (overwrite files).
