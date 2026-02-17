#!/usr/bin/env python3
"""
Pomodoro Visualizer - Main CLI
🍅 Pomodoro timer with visual analytics

SECURITY MANIFEST:
- Environment variables accessed: NOTIFICATION_ENABLED (optional)
- External endpoints called: none (local only)
- Local files written: data/pomodoro.db, data/*.png
- Local files read: data/pomodoro.db, templates/*
"""

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "pomodoro.db"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)


def init_db():
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            planned_duration INTEGER DEFAULT 25,
            actual_duration INTEGER,
            completed BOOLEAN DEFAULT 0,
            task_id TEXT,
            interruption_reason TEXT,
            date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_pomodoros INTEGER DEFAULT 0,
            total_minutes INTEGER DEFAULT 0
        )
    """)
    
    # Config table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    # Set default daily goal if not exists
    cursor.execute("""
        INSERT OR IGNORE INTO config (key, value) VALUES ('daily_goal', '8')
    """)
    
    conn.commit()
    conn.close()


def get_db_connection():
    """Get database connection."""
    return sqlite3.connect(DB_PATH)


def generate_session_id():
    """Generate unique session ID."""
    return f"session_{int(time.time() * 1000)}"


def cmd_start(args):
    """Start a new Pomodoro session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now()
    session_id = generate_session_id()
    
    # Get task_id if task name provided
    task_id = None
    if args.task:
        # Check if task exists, create if not
        cursor.execute("SELECT id FROM tasks WHERE name = ?", (args.task,))
        result = cursor.fetchone()
        if result:
            task_id = result[0]
        else:
            task_id = f"task_{int(time.time() * 1000)}"
            cursor.execute(
                "INSERT INTO tasks (id, name) VALUES (?, ?)",
                (task_id, args.task)
            )
    
    # Insert new session
    cursor.execute("""
        INSERT INTO sessions (id, start_time, planned_duration, task_id, date)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, now.isoformat(), args.duration or 25, task_id, now.strftime("%Y-%m-%d")))
    
    conn.commit()
    conn.close()
    
    # Save current session info
    with open(DATA_DIR / ".current_session.json", "w") as f:
        json.dump({
            "id": session_id,
            "start_time": now.isoformat(),
            "duration": args.duration or 25,
            "task_id": task_id,
            "task_name": args.task
        }, f)
    
    duration = args.duration or 25
    print(f"🍅 Pomodoro started! {duration} minutes.")
    print(f"⏰ Timer set for {duration} minutes.")
    print(f"🎯 Task: {args.task or 'No task specified'}")
    
    if args.duration and args.duration > 0:
        # Run timer
        print(f"\n⏳ Focusing for {duration} minutes...")
        remaining = args.duration * 60
        while remaining > 0:
            mins, secs = divmod(remaining, 60)
            print(f"\r⏰ {mins:02d}:{secs:02d} remaining", end="")
            time.sleep(1)
            remaining -= 1
        
        print("\n\n🎉 Time's up! Pomodoro completed!")
        cmd_complete(argparse.Namespace())
    else:
        print("\n💡 Use 'complete' command when done, or 'interrupt' if interrupted.")


def cmd_complete(args):
    """Mark current session as completed."""
    session_file = DATA_DIR / ".current_session.json"
    
    if not session_file.exists():
        print("❌ No active Pomodoro session found. Start one first!")
        return
    
    with open(session_file, "r") as f:
        session = json.load(f)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now()
    start_time = datetime.fromisoformat(session["start_time"])
    actual_duration = int((now - start_time).total_seconds() / 60)
    
    cursor.execute("""
        UPDATE sessions 
        SET end_time = ?, actual_duration = ?, completed = 1
        WHERE id = ?
    """, (now.isoformat(), actual_duration, session["id"]))
    
    # Update task pomodoro count if task associated
    if session.get("task_id"):
        cursor.execute("""
            UPDATE tasks 
            SET completed_pomodoros = completed_pomodoros + 1,
                total_minutes = total_minutes + ?
            WHERE id = ?
        """, (actual_duration, session["task_id"]))
    
    conn.commit()
    conn.close()
    
    # Remove current session file
    session_file.unlink()
    
    print(f"✅ Pomodoro completed! Duration: {actual_duration} minutes")
    print(f"📊 Great focus session!")


def cmd_interrupt(args):
    """Mark current session as interrupted."""
    session_file = DATA_DIR / ".current_session.json"
    
    if not session_file.exists():
        print("❌ No active Pomodoro session found. Start one first!")
        return
    
    with open(session_file, "r") as f:
        session = json.load(f)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now()
    start_time = datetime.fromisoformat(session["start_time"])
    actual_duration = int((now - start_time).total_seconds() / 60)
    
    cursor.execute("""
        UPDATE sessions 
        SET end_time = ?, actual_duration = ?, completed = 0, interruption_reason = ?
        WHERE id = ?
    """, (now.isoformat(), actual_duration, args.reason or "Unknown", session["id"]))
    
    conn.commit()
    conn.close()
    
    # Remove current session file
    session_file.unlink()
    
    print(f"⚠️ Pomodoro interrupted after {actual_duration} minutes")
    print(f"📝 Reason: {args.reason or 'Not specified'}")
    print(f"💪 Don't worry, every session counts! Try again when ready.")


def cmd_today(args):
    """Show today's Pomodoro summary."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Get completed sessions
    cursor.execute("""
        SELECT COUNT(*), SUM(actual_duration), SUM(completed)
        FROM sessions 
        WHERE date = ? AND completed = 1
    """, (today,))
    row = cursor.fetchone()
    completed_count = row[0] or 0
    total_minutes = row[1] or 0
    
    # Get interrupted sessions
    cursor.execute("""
        SELECT COUNT(*), SUM(actual_duration)
        FROM sessions 
        WHERE date = ? AND completed = 0 AND interruption_reason IS NOT NULL
    """, (today,))
    row = cursor.fetchone()
    interrupted_count = row[0] or 0
    interrupted_minutes = row[1] or 0
    
    # Get daily goal
    cursor.execute("SELECT value FROM config WHERE key = 'daily_goal'")
    daily_goal = int(cursor.fetchone()[0]) if cursor.fetchone() else 8
    
    conn.close()
    
    print(f"\n📅 Today's Pomodoro Report - {today}")
    print(f"=" * 40)
    print(f"✅ Completed: {completed_count} pomodoros ({total_minutes} min)")
    print(f"⚠️  Interrupted: {interrupted_count} ({interrupted_minutes} min)")
    print(f"🎯 Daily Goal: {completed_count}/{daily_goal}")
    
    if completed_count >= daily_goal:
        print(f"\n🎉 Daily goal achieved! Amazing work!")
    else:
        remaining = daily_goal - completed_count
        print(f"\n💪 {remaining} more to reach your daily goal!")
    
    # Progress bar
    progress = min(completed_count / daily_goal, 1.0)
    bar_length = 20
    filled = int(bar_length * progress)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"\n[{bar}] {completed_count}/{daily_goal}")


def cmd_week(args):
    """Show weekly Pomodoro summary."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get date range for this week
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    
    cursor.execute("""
        SELECT date, COUNT(*), SUM(actual_duration)
        FROM sessions 
        WHERE date >= ? AND completed = 1
        GROUP BY date
        ORDER BY date
    """, (week_start.strftime("%Y-%m-%d"),))
    
    rows = cursor.fetchall()
    
    # Get daily goal
    cursor.execute("SELECT value FROM config WHERE key = 'daily_goal'")
    daily_goal = int(cursor.fetchone()[0]) if cursor.fetchone() else 8
    
    conn.close()
    
    print(f"\n📊 Weekly Pomodoro Report")
    print(f"=" * 40)
    print(f"📆 Week of {week_start.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}")
    print()
    
    if not rows:
        print("📝 No completed Pomodoros this week yet!")
        return
    
    total_pomodoros = 0
    total_minutes = 0
    
    for date, count, minutes in rows:
        total_pomodoros += count
        total_minutes += minutes or 0
        day_name = datetime.strptime(date, "%Y-%m-%d").strftime("%a")
        
        # Mini bar
        progress = min(count / daily_goal, 1.0)
        bar_length = 10
        filled = int(bar_length * progress)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        print(f"{day_name} {date}: {count} 🍅 ({minutes or 0} min) [{bar}]")
    
    print()
    print(f"📈 Week Total: {total_pomodoros} pomodoros, {total_minutes} minutes")
    print(f"🎯 Daily Average: {total_pomodoros / 7:.1f} pomodoros/day")


def cmd_heatmap(args):
    """Generate GitHub-style heatmap for the month."""
    import math
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    year = args.year or datetime.now().year
    month = args.month or datetime.now().month
    
    # Get all sessions for the month
    cursor.execute("""
        SELECT date, COUNT(*), SUM(actual_duration)
        FROM sessions 
        WHERE date LIKE ? AND completed = 1
        GROUP BY date
        ORDER BY date
    """, (f"{year}-{month:02d}%",))
    
    rows = cursor.fetchall()
    
    # Get daily goal
    cursor.execute("SELECT value FROM config WHERE key = 'daily_goal'")
    daily_goal = int(cursor.fetchone()[0]) if cursor.fetchone() else 8
    
    conn.close()
    
    # Build date map
    date_map = {}
    for date, count, minutes in rows:
        date_map[date] = {"count": count, "minutes": minutes or 0}
    
    # Get month info
    first_day = datetime(year, month, 1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    print(f"\n🔥 Pomodoro Heatmap - {year}/{month:02d}")
    print("=" * 50)
    
    # Print header
    print(f"{'Mon':<5} {'Tue':<5} {'Wed':<5} {'Thu':<5} {'Fri':<5} {'Sat':<5} {'Sun':<5}")
    
    # Calculate starting position
    start_weekday = first_day.weekday()  # 0 = Monday
    
    # Generate calendar rows
    current = first_day
    day_num = 1
    max_day = last_day.day
    
    # Create grid
    grid = [["." for _ in range(7)] for _ in range(6)]
    
    for week in range(6):
        for day in range(7):
            idx = week * 7 + day
            
            if idx >= start_weekday and day_num <= max_day:
                date_str = f"{year}-{month:02d}-{day_num:02d}"
                
                if date_str in date_map:
                    count = date_map[date_str]["count"]
                    if count >= daily_goal:
                        grid[week][day] = "🟢"  # Goal achieved
                    elif count >= daily_goal * 0.5:
                        grid[week][day] = "🟡"  # Halfway
                    elif count > 0:
                        grid[week][day] = "🟠"  # Started
                    else:
                        grid[week][day] = "⚪"  # No data
                else:
                    grid[week][day] = "⬜"  # No session
                
                day_num += 1
    
    # Print grid
    for week in range(6):
        row = grid[week]
        has_content = any(c != "." for c in row)
        if has_content or week < 5:
            print(" ".join(row))
    
    # Legend
    print()
    print("Legend:")
    print(f"  🟢 Goal achieved ({daily_goal}+)")
    print(f"  🟡 Halfway ({daily_goal//2}-{daily_goal-1})")
    print(f"  🟠 Started (1-{daily_goal//2})")
    print(f"  ⬜ No sessions")
    
    # Summary
    total_pomodoros = sum(d["count"] for d in date_map.values())
    total_minutes = sum(d["minutes"] for d in date_map.values())
    active_days = len(date_map)
    
    print()
    print(f"📊 Month Summary:")
    print(f"  Total: {total_pomodoros} 🍅 ({total_minutes} min)")
    print(f"  Active days: {active_days}/{last_day.day}")
    print(f"  Daily avg: {total_minutes / active_days:.0f} min (on active days)")


def cmd_task(args):
    """Manage tasks."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if args.task_command == "add":
        if not args.name:
            print("❌ Please provide a task name")
            return
        
        task_id = f"task_{int(time.time() * 1000)}"
        cursor.execute(
            "INSERT INTO tasks (id, name) VALUES (?, ?)",
            (task_id, args.name)
        )
        conn.commit()
        print(f"✅ Task '{args.name}' added!")
    
    elif args.task_command == "list":
        cursor.execute("""
            SELECT name, completed_pomodoros, total_minutes, created_at
            FROM tasks
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        
        if not rows:
            print("📝 No tasks yet!")
            return
        
        print("\n📋 Your Tasks:")
        print("=" * 50)
        for name, pomodoros, minutes, created in rows:
            print(f"  • {name}")
            print(f"    🍅 {pomodoros} pomodoros | ⏱ {minutes} min | 📅 {created[:10]}")
            print()
    
    conn.close()


def cmd_config(args):
    """Manage configuration."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if args.config_command == "daily_goal":
        if args.value:
            cursor.execute(
                "INSERT OR REPLACE INTO config (key, value) VALUES ('daily_goal', ?)",
                (args.value,)
            )
            conn.commit()
            print(f"✅ Daily goal set to {args.value} pomodoros")
        else:
            cursor.execute("SELECT value FROM config WHERE key = 'daily_goal'")
            result = cursor.fetchone()
            print(f"📊 Current daily goal: {result[0] if result else 8} pomodoros")
    
    conn.close()


def cmd_export(args):
    """Export data."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, start_time, end_time, planned_duration, actual_duration, 
               completed, task_id, interruption_reason, date
        FROM sessions
        ORDER BY start_time DESC
    """)
    
    rows = cursor.fetchall()
    
    sessions = []
    for row in rows:
        sessions.append({
            "id": row[0],
            "start_time": row[1],
            "end_time": row[2],
            "planned_duration": row[3],
            "actual_duration": row[4],
            "completed": bool(row[5]),
            "task_id": row[6],
            "interruption_reason": row[7],
            "date": row[8]
        })
    
    conn.close()
    
    if args.format == "json":
        print(json.dumps(sessions, indent=2))
    else:
        print("Currently only JSON export is supported")


def main():
    parser = argparse.ArgumentParser(description="🍅 Pomodoro Visualizer")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start a Pomodoro session")
    start_parser.add_argument("--task", type=str, help="Task name")
    start_parser.add_argument("--duration", type=int, default=25, help="Duration in minutes")
    
    # Complete command
    subparsers.add_parser("complete", help="Complete current session")
    
    # Interrupt command
    interrupt_parser = subparsers.add_parser("interrupt", help="Interrupt current session")
    interrupt_parser.add_argument("--reason", type=str, help="Reason for interruption")
    
    # Today command
    subparsers.add_parser("today", help="Show today's summary")
    
    # Week command
    subparsers.add_parser("week", help="Show weekly summary")
    
    # Heatmap command
    heatmap_parser = subparsers.add_parser("heatmap", help="Generate heatmap")
    heatmap_parser.add_argument("--year", type=int, help="Year")
    heatmap_parser.add_argument("--month", type=int, help="Month")
    
    # Task command
    task_parser = subparsers.add_parser("task", help="Manage tasks")
    task_parser.add_argument("task_command", choices=["add", "list"], help="Task command")
    task_parser.add_argument("--name", type=str, help="Task name")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_parser.add_argument("config_command", choices=["daily_goal"], help="Config command")
    config_parser.add_argument("--value", type=str, help="Config value")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export data")
    export_parser.add_argument("--format", choices=["json"], default="json", help="Export format")
    
    args = parser.parse_args()
    
    # Initialize database
    init_db()
    
    # Route to command
    if args.command == "start":
        cmd_start(args)
    elif args.command == "complete":
        cmd_complete(args)
    elif args.command == "interrupt":
        cmd_interrupt(args)
    elif args.command == "today":
        cmd_today(args)
    elif args.command == "week":
        cmd_week(args)
    elif args.command == "heatmap":
        cmd_heatmap(args)
    elif args.command == "task":
        cmd_task(args)
    elif args.command == "config":
        cmd_config(args)
    elif args.command == "export":
        cmd_export(args)
    else:
        parser.print_help()
        print("\n💡 Quick Examples:")
        print("  python3 scripts/pomodoro.py start --task 'Writing'")
        print("  python3 scripts/pomodoro.py today")
        print("  python3 scripts/pomodoro.py heatmap")


if __name__ == "__main__":
    main()
