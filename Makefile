.PHONY: all test check-db setup-local clean

all: test check-db

test:
	python3 tests/test_sql.py

check-db:
	@python3 -c "\
import sqlite3, sys, os, tempfile; \
db=tempfile.mktemp(suffix='.db'); \
con=sqlite3.connect(db); \
con.executescript(open('agent/schema.sql').read()); \
tables={r[0] for r in con.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")}; \
indexes={r[0] for r in con.execute(\"SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'\")}; \
con.close(); os.remove(db); \
fails=[]; \
[print('PASS: table '+t) or None if t in tables else fails.append(t) or print('FAIL: table '+t) for t in ['anchors','body_status','events','habit_logs','settings','tasks']]; \
[print('PASS: index '+i) or None if i in indexes else fails.append(i) or print('FAIL: index '+i) for i in ['idx_body_status_date','idx_habit_logs_anchor_date','idx_habit_logs_date','idx_anchors_active','idx_events_start']]; \
sys.exit(1 if fails else 0) \
"

setup-local:
	@mkdir -p /tmp/nanoclaw-test-group/.claude/skills/life-secretary/migrations
	@mkdir -p /tmp/nanoclaw-test-group/.claude/skills/life-secretary/plans
	@cp -f agent/CLAUDE.md /tmp/nanoclaw-test-group/CLAUDE.md
	@cp -f agent/SKILL.md /tmp/nanoclaw-test-group/.claude/skills/life-secretary/SKILL.md
	@cp -f agent/schema.sql /tmp/nanoclaw-test-group/.claude/skills/life-secretary/schema.sql
	@cp -f agent/init-db.sh /tmp/nanoclaw-test-group/.claude/skills/life-secretary/init-db.sh
	@chmod +x /tmp/nanoclaw-test-group/.claude/skills/life-secretary/init-db.sh
	@cp -r agent/migrations/. /tmp/nanoclaw-test-group/.claude/skills/life-secretary/migrations/ 2>/dev/null || true
	@cp -f agent/plans/fitness-plan.md /tmp/nanoclaw-test-group/.claude/skills/life-secretary/plans/fitness-plan.md 2>/dev/null || true
	@echo "Local test group ready at /tmp/nanoclaw-test-group/"
	@echo "To test: cd /tmp/nanoclaw-test-group && claude"

clean:
	rm -rf /tmp/nanoclaw-test-group/
	rm -f /tmp/life-secretary-check-*.db
	rm -f /tmp/life-secretary-test.db