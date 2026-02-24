CREATE TABLE IF NOT EXISTS anchors (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  days_of_week TEXT NOT NULL,
  time_start TEXT NOT NULL,
  time_end TEXT NOT NULL,
  protection_level TEXT NOT NULL,
  min_frequency INTEGER NOT NULL,
  degradation_a INTEGER NOT NULL,
  degradation_a_desc TEXT NOT NULL,
  degradation_b INTEGER NOT NULL,
  degradation_b_desc TEXT NOT NULL,
  degradation_c INTEGER NOT NULL,
  degradation_c_desc TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS body_status (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT UNIQUE NOT NULL,
  status TEXT NOT NULL,
  notes TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS habit_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  anchor_id TEXT NOT NULL,
  date TEXT NOT NULL,
  completed INTEGER NOT NULL DEFAULT 0,
  level TEXT,
  notes TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (anchor_id) REFERENCES anchors(id) ON DELETE CASCADE,
  UNIQUE(anchor_id, date)
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  start_time TEXT NOT NULL,
  end_time TEXT NOT NULL,
  start_date TEXT,
  end_date TEXT,
  is_all_day INTEGER DEFAULT 0,
  event_type TEXT NOT NULL DEFAULT 'work',
  anchor_id TEXT,
  habit_id TEXT,
  degradation_level TEXT,
  recurrence_rule TEXT,
  recurring_event_id TEXT,
  timezone TEXT DEFAULT 'Asia/Shanghai',
  description TEXT,
  local_updated_at TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (anchor_id) REFERENCES anchors(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  estimated_minutes INTEGER,
  deadline TEXT,
  priority INTEGER DEFAULT 3,
  status TEXT DEFAULT 'pending',
  scheduled_event_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (scheduled_event_id) REFERENCES events(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_body_status_date ON body_status(date);
CREATE INDEX IF NOT EXISTS idx_habit_logs_anchor_date ON habit_logs(anchor_id, date);
CREATE INDEX IF NOT EXISTS idx_habit_logs_date ON habit_logs(date);
CREATE INDEX IF NOT EXISTS idx_anchors_active ON anchors(active);
CREATE INDEX IF NOT EXISTS idx_events_start ON events(start_time);
