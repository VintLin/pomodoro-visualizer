# 🍅 Pomodoro Visualizer

A local OpenClaw skill for Pomodoro timer tracking with visual analytics.

## Features

- 🍅 **Pomodoro Timer** - Start 25-minute focus sessions with customizable duration
- 📊 **Visual Analytics** - Generate GitHub-style heatmaps and productivity charts
- 📈 **Session Tracking** - Record completed sessions, interruptions, and task associations
- 🎯 **Goal Tracking** - Set daily targets and track achievement rate

## Installation

```bash
# Clone to your OpenClaw skills directory
mkdir -p ~/.openclaw/skills/pomodoro-visualizer
git clone https://github.com/VintLin/pomodoro-visualizer.git ~/.openclaw/skills/pomodoro-visualizer

# Install dependencies
cd ~/.openclaw/skills/pomodoro-visualizer
pip install -r requirements.txt
```

## Usage

### Timer Commands

```bash
# Start a 25-minute Pomodoro
python3 scripts/pomodoro.py start

# Start with task association
python3 scripts/pomodoro.py start --task "Write documentation" --duration 25

# Complete current session
python3 scripts/pomodoro.py complete

# Interrupt session with reason
python3 scripts/pomodoro.py interrupt --reason "Emergency meeting"
```

### Query Commands

```bash
# Today's summary
python3 scripts/pomodoro.py today

# This week's summary
python3 scripts/pomodoro.py week

# Generate heatmap for current month
python3 scripts/pomodoro.py heatmap

# Generate heatmap for specific month
python3 scripts/pomodoro.py heatmap --year 2026 --month 2
```

### Management Commands

```bash
# Add a new task
python3 scripts/pomodoro.py task add "Project A"

# List all tasks
python3 scripts/pomodoro.py task list

# Set daily goal
python3 scripts/pomodoro.py config daily_goal 8

# Export data as JSON
python3 scripts/pomodoro.py export --format json
```

## Trigger Words

- "开始番茄钟" / "start pomodoro"
- "开始25分钟专注" / "25分钟计时"
- "今天几个番茄" / "今日专注统计"
- "这周专注情况" / "weekly stats"
- "显示专注热力图" / "专注日历"

## OpenClaw Integration

Add to your OpenClaw configuration:

```json
{
  "skills": {
    "entries": {
      "pomodoro-visualizer": {
        "enabled": true
      }
    }
  }
}
```

## Data Storage

All data is stored locally in:
- `data/pomodoro.db` - SQLite database

No data is sent to external servers.

## License

MIT
