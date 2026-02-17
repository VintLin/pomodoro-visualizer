---
name: pomodoro-visualizer
description: Pomodoro timer with visual analytics - track focus sessions, generate heatmaps and productivity reports
homepage: https://github.com/VintLin/pomodoro-visualizer
metadata:
  openclaw:
    emoji: "🍅"
    os:
      - darwin
      - linux
    requires:
      bins:
        - python3
      env:
        - NOTIFICATION_ENABLED
    files:
      - scripts/*
---

# Pomodoro Visualizer

A local skill for Pomodoro timer tracking with visual analytics - track focus sessions, generate heatmaps and productivity reports.

## What it does

- 🍅 **Pomodoro Timer** - Start 25-minute focus sessions with customizable duration
- 📊 **Visual Analytics** - Generate GitHub-style heatmaps and productivity charts
- 📈 **Session Tracking** - Record completed sessions, interruptions, and task associations
- 🎯 **Goal Tracking** - Set daily targets and track achievement rate

## Core Flow

1. User starts a Pomodoro session with optional task association
2. Timer runs for specified duration (default 25 min)
3. On completion, session is recorded to SQLite database
4. User can query stats or generate visual reports
5. CLI outputs `REPORT_IMAGE:<path>` for chart generation

## CLI Commands

```bash
# Timer
python3 scripts/pomodoro.py start [--task "TaskName"] [--duration 25]
python3 scripts/pomodoro.py complete
python3 scripts/pomodoro.py interrupt [--reason "原因"]

# Query
python3 scripts/pomodoro.py today
python3 scripts/pomodoro.py week
python3 scripts/pomodoro.py heatmap [--year 2026] [--month 2]

# Management
python3 scripts/pomodoro.py task add "项目A"
python3 scripts/pomodoro.py task list
python3 scripts/pomodoro.py config daily_goal 8
python3 scripts/pomodoro.py export [--format json]
```

## Trigger Words

- "开始番茄钟" / "start pomodoro"
- "开始25分钟专注" / "25分钟计时"
- "今天几个番茄" / "今日专注统计"
- "这周专注情况" / "weekly stats"
- "显示专注热力图" / "专注日历"

## Dependencies

```bash
cd skills/pomodoro-visualizer
pip install -r requirements.txt
```

- Python 3.8+
- SQLite (built-in)
- Vega-Lite for chart generation (via chart-image skill or standalone)

## External Endpoints

| Endpoint | Data Sent |
|----------|-----------|
| None | This skill runs entirely offline |

## Security & Privacy

- All data stored locally in SQLite database
- No data uploaded to external servers
- No API calls, pure local operation
- No collection of personal information

## Trust Statement

This skill operates entirely offline and does not collect or transmit any user data. All focus session data stays local on your machine.

## Storage

- `data/pomodoro.db` (local SQLite)
- No automatic external sync
