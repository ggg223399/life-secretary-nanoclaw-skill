# life-secretary-nanoclaw-skill

个人日程管家 Nanoclaw Skill — SQLite 本地存储，16 个管理工具，习惯追踪，工作生活平衡。

---

## 安装

```bash
cd .claude/skills
git clone https://github.com/ggg223399/life-secretary-nanoclaw-skill life-secretary
```

## 部署

在 VPS 的 Claude Code 里运行：

```
/init-life-secretary
```

按提示操作：
1. 输入 group 文件夹名（默认 `life-secretary`）
2. 选择是否已有 Telegram 频道（有则提供 chat ID，没有则部署后运行 `/add-telegram`）

部署完成后，agent 文件会写入 `groups/{folder}/`，数据库在首次收到消息时自动初始化。

## 获取 Chat ID

部署时需要提供 Telegram chat ID。获取方法：

1. 在目标 Telegram 群组/聊天中向 NanoClaw bot 发送 `/chatid`
2. Bot 会回复 chat ID，格式为 `tg:XXXXXXXXXX`
3. 在部署提示输入 chat ID 时使用该值

## 更新

```bash
cd .claude/skills/life-secretary && git pull
```

然后重新发送任意消息，agent 会自动检测版本并执行迁移（数据完整保留）。

---

## Telegram 命令菜单（快捷操作）

在 Telegram 里输入 `/` 可弹出命令快捷菜单，无需手动打字。

### 配置方法
1. 打开 [@BotFather](https://t.me/BotFather)
2. 发送 `/setcommands`
3. 选择你的 bot
4. 粘贴以下命令列表并发送：

view_schedule - 查看日程（今天/本周/指定日期）
add_event - 添加事件（自然语言描述时间）
detect_conflicts - 检测日程冲突和SLA违规
weekly_review - 周回顾报告
view_habits - 查看习惯完成情况和连续性
log_body_status - 记录今日身体状态（绿/黄/红）
manage_anchor - 管理生活锚点（健身/冥想等）
manage_tasks - 任务增删改查
optimize_day - 优化今日任务排期
protect_focus - 创建专注时间块

> **提示**：命令菜单适合高频操作入口。发送命令后可追加参数，例如 `/add_event 明晚7点健身`；也可直接发送自然语言，效果相同。
---

## 工具使用说明

所有工具通过自然语言触发，发送到对应的 Telegram 群组即可。

### 日程管理

#### 1. view_schedule — 查看日程

```
看看今天日程
这周都有什么安排
明天的日程
```

返回按时间排序的事件列表。无事件时返回空日程提示。

#### 2. add_event — 添加事件

```
明晚7点健身
周四下午3点开评审会，持续1小时
今天上午10点到12点写报告
```

自动解析自然语言时间，创建成功后回显标题与起止时间。

#### 3. delete_event — 删除事件

```
删除今晚健身
取消周四的评审会
删除事件 <事件ID>
```

按标题模糊匹配或精确 ID 删除。

#### 4. detect_conflicts — 检测冲突

```
检查冲突
这周有没有SLA违规
今天日程有没有问题
```

检测四类问题：
- **overlap**：事件时间重叠
- **short_gap**：相邻事件间隔 < 15 分钟
- **anchor_squeezed**：工作事件挤占锚点时间窗口
- **sla_violation**：本周习惯完成次数不足 min_frequency

---

### 锚点管理

#### 5. manage_anchor — 管理生活锚点

```
创建健身锚点，周一三五晚上7点到8点，每周至少3次
列出所有锚点
删除健身锚点
把健身锚点改成每周至少2次
```

锚点是需要保护的固定生活事项（健身、冥想、阅读等）。

#### 6. protect_focus — 创建专注时间

```
明天上午10点到12点设为专注时间
下午留90分钟深度工作
今天3点到5点不要打扰
```

创建 `event_type=focus` 的时间块，并自动检测与其他事件的冲突。

#### 7. manage_flex_block — 弹性时间块

```
创建一个本周可灵活安排的30分钟复盘块
列出弹性时间块
删除那个复盘弹性块
```

弹性块（`event_type=flex`）可在时间窗口内自由移动，不占固定时间。

#### 8. set_degradation — 设置降级方案

```
把健身锚点改成A60/B30/C15
设置冥想锚点：A版本20分钟完整冥想，B版本10分钟，C版本5分钟呼吸练习
```

A/B/C 三档对应状态好/一般/差时的执行版本，保证习惯不断档。

---

### 习惯追踪

#### 9. log_body_status — 记录身体状态

```
今天状态绿灯
今天黄灯，有点疲劳
今天红灯，需要休息
```

- 🟢 绿灯：状态好，按计划执行
- 🟡 黄灯：一般，考虑降级方案
- 🔴 红灯：差，执行保底版或休息

同一天重复记录会自动覆盖。

#### 10. view_habits — 查看习惯完成情况

```
看看这周习惯完成情况
我最近连续性怎么样
健身锚点的完成率
```

返回各锚点的完成次数、连续天数（streak）、本周是否达标。

#### 11. weekly_review — 周回顾

```
周回顾
给我上周报告
这周总结
```

输出：
- 事件类型分布（工作/锚点/专注/弹性）
- 各习惯完成率
- 任务完成率 + 未完成/逾期任务
- 下周建议

---

### 任务管理

#### 12. manage_tasks — 任务增删改查

```
创建任务：写周报，优先级2，预计60分钟
列出待办任务
把写周报标记为完成
删除任务 <任务ID>
```

优先级 1（最高）到 5（最低）。

#### 13. schedule_task — 任务排期

```
把写周报安排到明天上午10点
给这个任务自动排期
```

手动指定时间或自动寻找空档，排期后任务状态变为 `scheduled`，同时在 events 表创建对应事件。

#### 14. estimate_task_time — 估算任务时间

```
这个任务优先级2，要多久
估算「整理需求文档」的时间
```

| 优先级 | 建议时长 |
|--------|----------|
| 1 | 90 分钟 |
| 2 | 60 分钟 |
| 3 | 30 分钟 |
| 4 | 20 分钟 |
| 5 | 15 分钟 |

#### 15. optimize_day — 优化今日日程

```
今天怎么安排
优化今天日程
帮我排一下今天的任务
```

读取当天已有事件 → 计算空档 → 按优先级和截止日期推荐任务执行顺序。

#### 16. planner_settings — 排期配置

```
工作时段改成9:30到18:30
查看当前提醒设置
把默认任务时长改成45分钟
```

可配置项：
- `workStart` / `workEnd`：工作时段
- `breakMinutes`：休息缓冲时间
- `defaultTaskDurationMinutes`：默认任务时长
- `defaultReminderOffsetMinutes`：提醒提前量

---

## 内置自检（5条）

部署后发送以下消息验证功能正常：

```
看看今天日程
明晚7点健身
创建健身锚点，周一三五晚上7点到8点，每周至少3次
今天状态绿灯
看看这周习惯完成情况
```

---

## 数据安全 & 迁移

- **数据库路径**：`/workspace/group/life-secretary.db`（容器内），对应宿主机 `groups/{folder}/life-secretary.db`
- **re-deploy 数据保留**：数据库文件不在部署覆盖范围内，re-deploy 只更新 skill 文件
- **schema 升级**：`init-db.sh` 每次运行时检查 `schema_version`
  - 已是最新版本 → 直接退出，零开销
  - 需要升级 → 自动备份（`life-secretary.db.bak-vN`）→ 顺序执行 `migrations/00N.sql` → 更新版本号
- **迁移文件**：`agent/migrations/` 目录，当前为空（v1 是基线）
- **添加迁移**：新增 `migrations/002.sql`，更新 `init-db.sh` 中的 `LATEST_VERSION=2`

### 迁移文件格式

```sql
-- migrations/002.sql
BEGIN TRANSACTION;
ALTER TABLE events ADD COLUMN tags TEXT;
ALTER TABLE tasks ADD COLUMN tags TEXT;
COMMIT;
```

---

## 仓库结构

```
life-secretary-nanoclaw-skill/
├── SKILL.md                    # 部署技能（Phase-based，/init-life-secretary 命令）
├── agent/
│   ├── SKILL.md                # 运行时技能（16 工具操作指南）
│   ├── CLAUDE.md               # Group 级触发路由
│   ├── schema.sql              # SQLite 6 表结构
│   ├── init-db.sh              # 数据库初始化 + 迁移脚本
│   ├── sqlite3                 # Python sqlite3 wrapper（无需系统包）
│   └── migrations/
│       └── .gitkeep            # v1 为基线，迁移文件放这里
│   └── plans/
│       └── fitness-plan.md     # 内置健身计划参考
├── tests/
│   └── test_sql.py             # SQL 逻辑 + 迁移测试（108 checks）
└── README.md
```

## License

MIT
