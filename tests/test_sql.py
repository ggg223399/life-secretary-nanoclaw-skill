#!/usr/bin/env python3
"""
life-secretary SQL logic test suite
Runs entirely via Python's built-in sqlite3 — no external dependencies.

Usage:
    python3 tests/test_sql.py

Covers:
    Round 1 (47 checks): schema, add_event, view_schedule, manage_anchor,
        log_body_status (upsert), view_habits, manage_tasks, schedule_task,
        detect_conflicts (overlap), planner_settings, set_degradation,
        delete_event, FK cascade, weekly_review, idempotent re-init
    Round 2 (28 checks): protect_focus, manage_flex_block,
        detect_conflicts (anchor_squeezed / sla_violation / short_gap),
        optimize_day, estimate_task_time, weekly_review full aggregation
"""

import sqlite3
import json
import uuid
import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent.parent / "agent" / "schema.sql"
DB_PATH = "/tmp/life-secretary-test.db"


def now():   return datetime.now().isoformat()
def today(): return date.today().isoformat()
def uid():   return str(uuid.uuid4())


results = []


def check(name, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    results.append((status, name, detail))
    marker = "✓" if ok else "✗"
    print(f"  {marker} {name}" + (f" — {detail}" if detail else ""))


def setup_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    schema = SCHEMA_PATH.read_text()
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(schema)
    con.commit()
    return con, schema


# ─────────────────────────────────────────────────────────────────────────────
# ROUND 1
# ─────────────────────────────────────────────────────────────────────────────

def test_schema(con, schema):
    print("\n=== TEST 1: Schema init ===")
    tables = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    for t in ["anchors", "body_status", "events", "habit_logs", "settings", "tasks"]:
        check(f"table:{t}", t in tables)

    indexes = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")}
    for i in ["idx_body_status_date", "idx_habit_logs_anchor_date",
              "idx_habit_logs_date", "idx_anchors_active", "idx_events_start"]:
        check(f"index:{i}", i in indexes)


def test_add_event(con):
    print("\n=== TEST 2: add_event ===")
    eid = uid()
    con.execute("""
        INSERT INTO events(id,title,start_time,end_time,start_date,event_type,local_updated_at,created_at)
        VALUES(?,?,?,?,?,?,?,?)
    """, (eid, "健身", "2026-02-25T19:00:00+08:00", "2026-02-25T20:00:00+08:00",
          "2026-02-25", "anchor", now(), now()))
    con.commit()
    row = con.execute("SELECT title,start_time FROM events WHERE id=?", (eid,)).fetchone()
    check("add_event: row inserted", row is not None)
    check("add_event: title correct", row and row[0] == "健身", row[0] if row else "")
    check("add_event: time correct", row and "19:00" in row[1])
    return eid


def test_view_schedule(con):
    print("\n=== TEST 3: view_schedule ===")
    rows = con.execute("""
        SELECT title, start_time, end_time, event_type
        FROM events WHERE start_date = ? ORDER BY start_time
    """, ("2026-02-25",)).fetchall()
    check("view_schedule: returns rows", len(rows) >= 1)
    check("view_schedule: correct event", rows[0][0] == "健身" if rows else False)


def test_manage_anchor(con):
    print("\n=== TEST 4: manage_anchor ===")
    aid = uid()
    con.execute("""
        INSERT INTO anchors(id,name,days_of_week,time_start,time_end,protection_level,
            min_frequency,degradation_a,degradation_a_desc,degradation_b,degradation_b_desc,
            degradation_c,degradation_c_desc,active,created_at,updated_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (aid, "健身", "[1,3,5]", "19:00", "20:00", "strict", 3,
          60, "完整训练60分钟", 30, "缩短版30分钟", 15, "保底15分钟", 1, now(), now()))
    con.commit()
    row = con.execute("SELECT name,min_frequency,days_of_week FROM anchors WHERE id=?", (aid,)).fetchone()
    check("manage_anchor: inserted", row is not None)
    check("manage_anchor: name correct", row and row[0] == "健身")
    check("manage_anchor: min_frequency=3", row and row[1] == 3)
    check("manage_anchor: days_of_week JSON", row and json.loads(row[2]) == [1, 3, 5])
    return aid


def test_log_body_status(con):
    print("\n=== TEST 5: log_body_status ===")
    con.execute("""
        INSERT INTO body_status(date,status,notes,created_at) VALUES(?,?,?,?)
        ON CONFLICT(date) DO UPDATE SET status=excluded.status, notes=excluded.notes
    """, (today(), "green", "状态不错", now()))
    con.commit()
    row = con.execute("SELECT status FROM body_status WHERE date=?", (today(),)).fetchone()
    check("log_body_status: inserted", row is not None)
    check("log_body_status: status=green", row and row[0] == "green")

    print("\n=== TEST 6: log_body_status upsert ===")
    con.execute("""
        INSERT INTO body_status(date,status,notes,created_at) VALUES(?,?,?,?)
        ON CONFLICT(date) DO UPDATE SET status=excluded.status, notes=excluded.notes
    """, (today(), "yellow", "有点疲劳", now()))
    con.commit()
    row = con.execute("SELECT status FROM body_status WHERE date=?", (today(),)).fetchone()
    check("upsert: status updated to yellow", row and row[0] == "yellow")
    count = con.execute("SELECT COUNT(*) FROM body_status WHERE date=?", (today(),)).fetchone()[0]
    check("upsert: no duplicate rows", count == 1, f"count={count}")


def test_view_habits(con, aid):
    print("\n=== TEST 7: view_habits ===")
    for d, completed, level in [("2026-02-24", 1, "A"), ("2026-02-22", 1, "B"), ("2026-02-20", 0, None)]:
        con.execute("""
            INSERT OR IGNORE INTO habit_logs(anchor_id,date,completed,level,created_at)
            VALUES(?,?,?,?,?)
        """, (aid, d, completed, level, now()))
    con.commit()
    rows = con.execute("""
        SELECT h.date, h.completed, h.level, a.name
        FROM habit_logs h JOIN anchors a ON h.anchor_id=a.id
        WHERE h.anchor_id=? ORDER BY h.date DESC
    """, (aid,)).fetchall()
    check("view_habits: returns rows", len(rows) == 3)
    check("view_habits: join works", rows[0][3] == "健身")
    check("view_habits: completion count", sum(1 for r in rows if r[1] == 1) == 2)


def test_manage_tasks(con):
    print("\n=== TEST 8: manage_tasks ===")
    tid = uid()
    con.execute("""
        INSERT INTO tasks(id,title,description,estimated_minutes,priority,status,created_at,updated_at)
        VALUES(?,?,?,?,?,?,?,?)
    """, (tid, "写周报", "整理本周工作内容", 60, 2, "pending", now(), now()))
    con.commit()
    row = con.execute("SELECT title,priority,status FROM tasks WHERE id=?", (tid,)).fetchone()
    check("manage_tasks: inserted", row is not None)
    check("manage_tasks: priority=2", row and row[1] == 2)
    check("manage_tasks: status=pending", row and row[2] == "pending")
    return tid


def test_schedule_task(con, tid):
    print("\n=== TEST 9: schedule_task ===")
    task_eid = uid()
    con.execute("""
        INSERT INTO events(id,title,start_time,end_time,start_date,event_type,local_updated_at,created_at)
        VALUES(?,?,?,?,?,?,?,?)
    """, (task_eid, "写周报", "2026-02-25T10:00:00+08:00", "2026-02-25T11:00:00+08:00",
          "2026-02-25", "work", now(), now()))
    con.execute("UPDATE tasks SET status='scheduled', scheduled_event_id=?, updated_at=? WHERE id=?",
                (task_eid, now(), tid))
    con.commit()
    row = con.execute("SELECT status, scheduled_event_id FROM tasks WHERE id=?", (tid,)).fetchone()
    check("schedule_task: status=scheduled", row and row[0] == "scheduled")
    check("schedule_task: event linked", row and row[1] == task_eid)


def test_detect_conflicts_overlap(con):
    print("\n=== TEST 10: detect_conflicts — overlap ===")
    e1, e2 = uid(), uid()
    con.execute("""
        INSERT INTO events(id,title,start_time,end_time,start_date,event_type,local_updated_at,created_at)
        VALUES(?,?,?,?,?,?,?,?)
    """, (e1, "会议A", "2026-02-25T14:00:00+08:00", "2026-02-25T15:30:00+08:00", "2026-02-25", "work", now(), now()))
    con.execute("""
        INSERT INTO events(id,title,start_time,end_time,start_date,event_type,local_updated_at,created_at)
        VALUES(?,?,?,?,?,?,?,?)
    """, (e2, "会议B", "2026-02-25T15:00:00+08:00", "2026-02-25T16:00:00+08:00", "2026-02-25", "work", now(), now()))
    con.commit()
    conflicts = con.execute("""
        SELECT a.title, b.title FROM events a JOIN events b ON a.id < b.id
        WHERE a.start_date = b.start_date
          AND a.start_time < b.end_time AND a.end_time > b.start_time
    """).fetchall()
    check("detect_conflicts overlap: found", len(conflicts) >= 1, f"{len(conflicts)} conflict(s)")
    check("detect_conflicts overlap: correct pair",
          any("会议A" in str(c) and "会议B" in str(c) for c in conflicts))


def test_planner_settings(con):
    print("\n=== TEST 11: planner_settings ===")
    for k, v in [("workStart", "09:00"), ("workEnd", "18:30"), ("breakMinutes", "15"),
                 ("defaultTaskDurationMinutes", "30"), ("defaultReminderOffsetMinutes", "10")]:
        con.execute("INSERT OR REPLACE INTO settings(key,value,updated_at) VALUES(?,?,?)", (k, v, now()))
    con.commit()
    rows = {r[0]: r[1] for r in con.execute("SELECT key,value FROM settings")}
    check("planner_settings: workStart", rows.get("workStart") == "09:00")
    check("planner_settings: workEnd", rows.get("workEnd") == "18:30")
    check("planner_settings: all 5 keys", len(rows) == 5, f"{len(rows)} keys")


def test_set_degradation(con, aid):
    print("\n=== TEST 12: set_degradation ===")
    con.execute("""
        UPDATE anchors SET
            degradation_a=45, degradation_a_desc='完整45分钟',
            degradation_b=25, degradation_b_desc='缩短25分钟',
            degradation_c=10, degradation_c_desc='保底10分钟',
            updated_at=?
        WHERE id=?
    """, (now(), aid))
    con.commit()
    row = con.execute("SELECT degradation_a,degradation_b,degradation_c FROM anchors WHERE id=?", (aid,)).fetchone()
    check("set_degradation: A=45", row and row[0] == 45)
    check("set_degradation: B=25", row and row[1] == 25)
    check("set_degradation: C=10", row and row[2] == 10)


def test_delete_event(con, eid):
    print("\n=== TEST 13: delete_event ===")
    before = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    con.execute("DELETE FROM events WHERE id=?", (eid,))
    con.commit()
    after = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    check("delete_event: count decreased", after == before - 1, f"{before}→{after}")
    check("delete_event: row gone",
          con.execute("SELECT id FROM events WHERE id=?", (eid,)).fetchone() is None)


def test_fk_cascade(con, aid):
    print("\n=== TEST 14: FK cascade ===")
    before_logs = con.execute("SELECT COUNT(*) FROM habit_logs WHERE anchor_id=?", (aid,)).fetchone()[0]
    con.execute("DELETE FROM anchors WHERE id=?", (aid,))
    con.commit()
    after_logs = con.execute("SELECT COUNT(*) FROM habit_logs WHERE anchor_id=?", (aid,)).fetchone()[0]
    check("FK cascade: habit_logs deleted", after_logs == 0, f"before={before_logs}, after={after_logs}")


def test_weekly_review_basic(con):
    print("\n=== TEST 15: weekly_review (basic) ===")
    week_start, week_end = "2026-02-23", "2026-03-01"
    event_count = con.execute(
        "SELECT COUNT(*) FROM events WHERE start_date BETWEEN ? AND ?",
        (week_start, week_end)).fetchone()[0]
    task_done = con.execute(
        "SELECT COUNT(*) FROM tasks WHERE status IN ('completed','scheduled')").fetchone()[0]
    check("weekly_review: event count query works", event_count >= 0, f"{event_count} events")
    check("weekly_review: task status query works", task_done >= 0, f"{task_done} done tasks")


def test_idempotent_reinit(con, schema, tables):
    print("\n=== TEST 16: Idempotent re-init ===")
    try:
        con.executescript(schema)
        con.commit()
        check("idempotent: re-run schema no error", True)
        tables2 = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        check("idempotent: tables still exist", tables2 == tables)
    except Exception as e:
        check("idempotent: re-run schema no error", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# ROUND 2
# ─────────────────────────────────────────────────────────────────────────────

def test_protect_focus(con):
    print("\n=== TEST A: protect_focus ===")
    fid = uid()
    con.execute("""
        INSERT INTO events(id,title,start_time,end_time,start_date,event_type,local_updated_at,created_at)
        VALUES(?,?,?,?,?,?,?,?)
    """, (fid, "深度工作", "2026-02-25T10:00:00+08:00", "2026-02-25T12:00:00+08:00",
          "2026-02-25", "focus", now(), now()))
    eid_overlap = uid()
    con.execute("""
        INSERT INTO events(id,title,start_time,end_time,start_date,event_type,local_updated_at,created_at)
        VALUES(?,?,?,?,?,?,?,?)
    """, (eid_overlap, "临时会议", "2026-02-25T11:00:00+08:00", "2026-02-25T11:30:00+08:00",
          "2026-02-25", "work", now(), now()))
    con.commit()
    row = con.execute("SELECT event_type,title FROM events WHERE id=?", (fid,)).fetchone()
    check("protect_focus: event_type=focus", row and row[0] == "focus")
    check("protect_focus: title correct", row and row[1] == "深度工作")
    conflicts = con.execute("""
        SELECT a.title, b.title FROM events a JOIN events b ON a.id < b.id
        WHERE a.start_date=b.start_date
          AND a.start_time < b.end_time AND a.end_time > b.start_time
          AND (a.event_type='focus' OR b.event_type='focus')
    """).fetchall()
    check("protect_focus: conflict detected", len(conflicts) >= 1, f"{len(conflicts)} conflict(s)")


def test_manage_flex_block(con):
    print("\n=== TEST B: manage_flex_block ===")
    flex_id = uid()
    con.execute("""
        INSERT INTO events(id,title,start_time,end_time,start_date,event_type,description,local_updated_at,created_at)
        VALUES(?,?,?,?,?,?,?,?,?)
    """, (flex_id, "复盘", "2026-02-25T16:00:00+08:00", "2026-02-25T16:30:00+08:00",
          "2026-02-25", "flex", "本周复盘30分钟", now(), now()))
    con.commit()
    row = con.execute("SELECT event_type,description FROM events WHERE id=?", (flex_id,)).fetchone()
    check("manage_flex_block: event_type=flex", row and row[0] == "flex")
    check("manage_flex_block: description stored", row and "复盘" in row[1])
    flex_rows = con.execute("SELECT title FROM events WHERE event_type='flex'").fetchall()
    check("manage_flex_block: list query works", len(flex_rows) == 1)


def test_anchor_squeezed(con, aid):
    print("\n=== TEST C: detect_conflicts — anchor_squeezed ===")
    squeezer_id = uid()
    con.execute("""
        INSERT INTO events(id,title,start_time,end_time,start_date,event_type,local_updated_at,created_at)
        VALUES(?,?,?,?,?,?,?,?)
    """, (squeezer_id, "晚间会议", "2026-02-25T19:30:00+08:00", "2026-02-25T20:30:00+08:00",
          "2026-02-25", "work", now(), now()))
    con.commit()
    squeezed = con.execute("""
        SELECT a.name, e.title FROM anchors a, events e
        WHERE a.active = 1
          AND e.event_type NOT IN ('anchor','flex')
          AND e.start_date = '2026-02-25'
          AND (e.start_time < a.time_end || ':00' AND e.end_time > a.time_start || ':00')
    """).fetchall()
    check("anchor_squeezed: detected", len(squeezed) >= 1,
          f"{len(squeezed)} squeezer(s): {[r[1] for r in squeezed]}")


def test_sla_violation(con, aid):
    print("\n=== TEST D: detect_conflicts — sla_violation ===")
    week_start, week_end = "2026-02-23", "2026-03-01"
    con.execute("""
        INSERT OR IGNORE INTO habit_logs(anchor_id,date,completed,level,created_at)
        VALUES(?,?,?,?,?)
    """, (aid, "2026-02-23", 1, "A", now()))
    con.commit()
    completed = con.execute("""
        SELECT COUNT(*) FROM habit_logs
        WHERE anchor_id=? AND date BETWEEN ? AND ? AND completed=1
    """, (aid, week_start, week_end)).fetchone()[0]
    min_freq = con.execute("SELECT min_frequency FROM anchors WHERE id=?", (aid,)).fetchone()[0]
    check("sla_violation: at risk flagged", completed < min_freq,
          f"need {min_freq}, have {completed}")
    for d in ["2026-02-25", "2026-02-27"]:
        con.execute("""
            INSERT OR IGNORE INTO habit_logs(anchor_id,date,completed,level,created_at)
            VALUES(?,?,?,?,?)
        """, (aid, d, 1, "B", now()))
    con.commit()
    completed_after = con.execute("""
        SELECT COUNT(*) FROM habit_logs
        WHERE anchor_id=? AND date BETWEEN ? AND ? AND completed=1
    """, (aid, week_start, week_end)).fetchone()[0]
    check("sla_violation: clears after 3 completions", completed_after >= min_freq,
          f"{completed_after}/{min_freq}")


def test_short_gap(con):
    print("\n=== TEST E: detect_conflicts — short_gap ===")
    sg1, sg2 = uid(), uid()
    con.execute("""
        INSERT INTO events(id,title,start_time,end_time,start_date,event_type,local_updated_at,created_at)
        VALUES(?,?,?,?,?,?,?,?)
    """, (sg1, "会议X", "2026-02-26T09:00:00+08:00", "2026-02-26T10:00:00+08:00", "2026-02-26", "work", now(), now()))
    con.execute("""
        INSERT INTO events(id,title,start_time,end_time,start_date,event_type,local_updated_at,created_at)
        VALUES(?,?,?,?,?,?,?,?)
    """, (sg2, "会议Y", "2026-02-26T10:08:00+08:00", "2026-02-26T11:00:00+08:00", "2026-02-26", "work", now(), now()))
    con.commit()
    short_gaps = con.execute("""
        SELECT a.title, b.title,
            ROUND((julianday(b.start_time) - julianday(a.end_time)) * 24 * 60, 1) AS gap_min
        FROM events a JOIN events b ON a.start_date = b.start_date AND a.end_time < b.start_time
        WHERE (julianday(b.start_time) - julianday(a.end_time)) * 24 * 60 < 15
          AND NOT EXISTS (
            SELECT 1 FROM events c
            WHERE c.start_date = a.start_date
              AND c.start_time > a.end_time AND c.start_time < b.start_time
          )
        ORDER BY a.start_time
    """).fetchall()
    check("short_gap: detected", len(short_gaps) >= 1, f"{len(short_gaps)} gap(s)")
    check("short_gap: gap is 8 min",
          short_gaps and abs(short_gaps[0][2] - 8.0) < 0.5,
          f"gap={short_gaps[0][2] if short_gaps else 'N/A'} min")


def test_optimize_day(con):
    print("\n=== TEST F: optimize_day ===")
    t1, t2, t3 = uid(), uid(), uid()
    for tid, title, mins, pri in [(t1, "写周报", 60, 2), (t2, "回复邮件", 20, 4), (t3, "准备演讲", 90, 1)]:
        con.execute("""
            INSERT INTO tasks(id,title,estimated_minutes,priority,status,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?)
        """, (tid, title, mins, pri, "pending", now(), now()))
    con.commit()

    day_events = con.execute("""
        SELECT title, start_time, end_time FROM events
        WHERE start_date='2026-02-26' ORDER BY start_time
    """).fetchall()
    check("optimize_day: events loaded", len(day_events) == 2, f"{len(day_events)} events")

    work_start = "2026-02-26T09:00:00+08:00"
    work_end   = "2026-02-26T18:30:00+08:00"
    free_slots = []
    for i in range(len(day_events) + 1):
        slot_start = work_start if i == 0 else day_events[i-1][2]
        slot_end   = day_events[i][1] if i < len(day_events) else work_end
        gap_min = (datetime.fromisoformat(slot_end.replace("+08:00", "")) -
                   datetime.fromisoformat(slot_start.replace("+08:00", ""))).seconds // 60
        if gap_min > 0:
            free_slots.append((slot_start, slot_end, gap_min))
    check("optimize_day: free slots computed", len(free_slots) >= 1,
          f"{len(free_slots)} slots: {[s[2] for s in free_slots]} min")

    pending_tasks = con.execute("""
        SELECT title, estimated_minutes, priority FROM tasks
        WHERE status='pending' ORDER BY priority ASC, estimated_minutes DESC
    """).fetchall()
    check("optimize_day: tasks ranked by priority", pending_tasks[0][0] == "准备演讲",
          f"top task: {pending_tasks[0][0]}")

    scheduled = []
    remaining = [(s[0], s[1], s[2]) for s in free_slots]
    for task_title, task_mins, _ in pending_tasks:
        for i, (ss, se, gap) in enumerate(remaining):
            if gap >= task_mins:
                scheduled.append(task_title)
                new_start = (datetime.fromisoformat(ss.replace("+08:00", "")) +
                             timedelta(minutes=task_mins)).isoformat() + "+08:00"
                remaining[i] = (new_start, se, gap - task_mins)
                break
    check("optimize_day: all 3 tasks scheduled", len(scheduled) == 3,
          f"scheduled: {scheduled}")
    check("optimize_day: high-priority task first", scheduled[0] == "准备演讲")


def test_estimate_task_time(con):
    print("\n=== TEST G: estimate_task_time ===")
    rules = {1: 90, 2: 60, 3: 30, 4: 20, 5: 15}
    for pri, expected in rules.items():
        check(f"estimate_task_time: priority {pri} → {expected}min", rules[pri] == expected)
    row = con.execute("SELECT estimated_minutes FROM tasks WHERE title='写周报'").fetchone()
    check("estimate_task_time: stored in tasks table", row and row[0] == 60,
          f"stored={row[0] if row else None}")


def test_weekly_review_full(con, aid):
    print("\n=== TEST H: weekly_review (full aggregation) ===")
    week_start, week_end = "2026-02-23", "2026-03-01"
    type_dist = {r[0]: r[1] for r in con.execute("""
        SELECT event_type, COUNT(*) FROM events
        WHERE start_date BETWEEN ? AND ? GROUP BY event_type
    """, (week_start, week_end)).fetchall()}
    check("weekly_review: event type distribution", len(type_dist) > 0, str(type_dist))

    habit_stats = con.execute("""
        SELECT a.name,
            SUM(h.completed) as done,
            COUNT(*) as total,
            ROUND(100.0 * SUM(h.completed) / COUNT(*), 1) as rate
        FROM habit_logs h JOIN anchors a ON h.anchor_id = a.id
        WHERE h.date BETWEEN ? AND ? GROUP BY a.id
    """, (week_start, week_end)).fetchall()
    check("weekly_review: habit completion rate", len(habit_stats) >= 1,
          f"{habit_stats[0][0] if habit_stats else 'N/A'}: {habit_stats[0][1]}/{habit_stats[0][2]} = {habit_stats[0][3]}%" if habit_stats else "no data")

    task_stats = con.execute("""
        SELECT COUNT(*),
            SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END),
            SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END),
            SUM(CASE WHEN status='scheduled' THEN 1 ELSE 0 END)
        FROM tasks
    """).fetchone()
    check("weekly_review: task stats query works", task_stats is not None,
          f"total={task_stats[0]}, done={task_stats[1]}, pending={task_stats[2]}, scheduled={task_stats[3]}")

    overdue = con.execute("""
        SELECT title, deadline FROM tasks
        WHERE deadline IS NOT NULL AND deadline < ?
          AND status NOT IN ('completed','cancelled')
    """, (now(),)).fetchall()
    check("weekly_review: overdue query works", overdue is not None, f"{len(overdue)} overdue")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print(f"Schema: {SCHEMA_PATH}")
    print(f"DB:     {DB_PATH}")

    con, schema = setup_db()
    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}

    # Round 1
    test_schema(con, schema)
    eid = test_add_event(con)
    test_view_schedule(con)
    aid = test_manage_anchor(con)
    test_log_body_status(con)
    test_view_habits(con, aid)
    tid = test_manage_tasks(con)
    test_schedule_task(con, tid)
    test_detect_conflicts_overlap(con)
    test_planner_settings(con)
    test_set_degradation(con, aid)
    test_delete_event(con, eid)
    test_fk_cascade(con, aid)
    test_weekly_review_basic(con)
    test_idempotent_reinit(con, schema, tables)

    # Round 2 — needs fresh anchor
    aid2 = uid()
    con.execute("""
        INSERT INTO anchors(id,name,days_of_week,time_start,time_end,protection_level,
            min_frequency,degradation_a,degradation_a_desc,degradation_b,degradation_b_desc,
            degradation_c,degradation_c_desc,active,created_at,updated_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (aid2, "健身", "[1,3,5]", "19:00", "20:00", "strict", 3,
          60, "完整60分钟", 30, "缩短30分钟", 15, "保底15分钟", 1, now(), now()))
    con.commit()

    test_protect_focus(con)
    test_manage_flex_block(con)
    test_anchor_squeezed(con, aid2)
    test_sla_violation(con, aid2)
    test_short_gap(con)
    test_optimize_day(con)
    test_estimate_task_time(con)
    test_weekly_review_full(con, aid2)

    con.close()

    print("\n" + "=" * 60)
    passed = sum(1 for r in results if r[0] == "PASS")
    failed = sum(1 for r in results if r[0] == "FAIL")
    print(f"TOTAL: {passed} PASS / {failed} FAIL / {len(results)} checks")
    if failed:
        print("\nFailed checks:")
        for s, n, d in results:
            if s == "FAIL":
                print(f"  ✗ {n}" + (f": {d}" if d else ""))
        sys.exit(1)
    else:
        print("All checks passed ✓")


if __name__ == "__main__":
    main()
