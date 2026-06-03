#!/usr/bin/env python3
"""
Watson Hermes Dashboard - Real-time TUI monitoring
Usage: ./dashboard.py [--refresh N] [--quit-on-escape]
"""

import curses
import subprocess
import json
import os
import time
from datetime import datetime
from pathlib import Path

# Configuration
HERMES_HOME = Path(os.environ.get('HERMES_HOME', '~/.hermes')).expanduser()
WATSON_HOME = Path('/home/juanbeck/Watson')
REFRESH_RATE = 2  # seconds

def get_cpu_usage():
    """Get CPU usage percentage"""
    try:
        result = subprocess.run(['grep', 'cpu', '/proc/stat'], capture_output=True, text=True)
        parts = result.stdout.strip().split()
        idle = int(parts[4])
        total = sum(int(x) for x in parts[1:8])
        return round((1 - idle/total) * 100, 1)
    except:
        return 0.0

def get_memory_usage():
    """Get memory usage"""
    try:
        result = subprocess.run(['free', '-m'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        mem_line = lines[1].split()
        total = int(mem_line[1])
        used = int(mem_line[2])
        return round(used, 0), round(total, 0), round((used/total)*100, 1)
    except:
        return 0, 0, 0.0

def get_gpu_stats():
    """Get NVIDIA GPU stats"""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', 
             '--format=csv,noheader'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(',')
            util = float(parts[0].strip().replace('%', ''))
            mem_used = int(parts[1].strip().replace(' MiB', ''))
            mem_total = int(parts[2].strip().replace(' MiB', ''))
            return util, mem_used, mem_total
    except:
        pass
    return 0, 0, 0

def get_active_sessions():
    """Get active Hermes sessions"""
    sessions = []
    try:
        result = subprocess.run(['pgrep', '-af', 'hermes'], capture_output=True, text=True)
        if result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                sessions.append(line[:60])
    except:
        pass
    return sessions

def get_cron_jobs():
    """Get cron job status"""
    jobs = []
    jobs_file = HERMES_HOME / 'cron' / 'jobs.json'
    try:
        if jobs_file.exists():
            with open(jobs_file) as f:
                data = json.load(f)
            for job in data.get('jobs', []):
                if job.get('enabled'):
                    next_run = job.get('next_run_at', '')[:19] if job.get('next_run_at') else 'N/A'
                    last_status = job.get('last_status', 'unknown')
                    jobs.append({
                        'name': job['name'],
                        'next': next_run,
                        'status': last_status
                    })
    except:
        pass
    return jobs

def get_token_stats():
    """Get recent token usage from ledger"""
    stats = {'input': 0, 'output': 0, 'cost': 0}
    try:
        # Get today's ledger
        today = datetime.now().strftime('%Y-%m-%d')
        ledger_file = WATSON_HOME / 'reports' / 'expenditure' / f'ledger-{today}.md'
        if ledger_file.exists():
            content = ledger_file.read_text()
            # Parse daily stats
            for line in content.split('\n'):
                if 'Daily Codex input tokens:' in line:
                    stats['input'] = int(line.split(':')[1].replace(',', '').strip())
                elif 'Daily Codex output tokens:' in line:
                    stats['output'] = int(line.split(':')[1].replace(',', '').strip())
                elif 'Daily Codex cost:' in line:
                    stats['cost'] = float(line.split(':')[1].strip().replace('$', ''))
    except:
        pass
    return stats

def get_context_window_usage():
    """Estimate context window usage"""
    # This would need to query the actual model state
    # For now, return placeholder
    return 0

def format_bytes(n):
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"

class Dashboard:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(0)  # Hide cursor
        self.stdscr.nodelay(True)  # Non-blocking input
        self.last_refresh = time.time()
        
    def draw_header(self):
        """Draw header bar"""
        height, width = self.stdscr.getmaxyx()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        header = f" Watson Hermes Dashboard | {now} | Refresh: {REFRESH_RATE}s | Press 'q' to quit "
        self.stdscr.attron(curses.A_REVERSE | curses.A_BOLD)
        self.stdscr.addstr(0, 0, header[:width-1].ljust(width-1))
        self.stdscr.attroff(curses.A_REVERSE | curses.A_BOLD)
        
    def draw_panel(self, y, x, width, height, title, content):
        """Draw a bordered panel"""
        # Create window for panel
        try:
            panel = curses.newwin(height, width, y, x)
            panel.box()
            
            # Title bar
            title_str = f" {title} ".center(width-2)
            panel.attron(curses.A_REVERSE)
            panel.addstr(0, 0, title_str[:width-1])
            panel.attroff(curses.A_REVERSE)
            
            # Content
            lines = content.split('\n')
            for i, line in enumerate(lines[:height-2]):
                try:
                    panel.addstr(i+1, 1, line[:width-2])
                except:
                    pass
            
            panel.refresh()
        except curses.error:
            pass

    def draw_system_panel(self, y, x, width, height):
        """Draw system resources panel"""
        cpu = get_cpu_usage()
        mem_used, mem_total, mem_pct = get_memory_usage()
        gpu_util, gpu_mem_used, gpu_mem_total = get_gpu_stats()
        
        content = f"""
  CPU Usage:     {cpu:>5.1f}%
  Memory:        {mem_used:>6.0f} / {mem_total:>6.0f} MB ({mem_pct:>5.1f}%)
  
  GPU (NVIDIA):
    Utilization: {gpu_util:>5.1f}%
    Memory:      {gpu_mem_used:>6} / {gpu_mem_total:>6} MiB
    VRAM Usage:  {round(gpu_mem_used/gpu_mem_total*100, 1) if gpu_mem_total > 0 else 0:>5.1f}%
        """
        
        # Color coding for CPU
        if cpu > 80:
            color = curses.COLOR_RED
        elif cpu > 50:
            color = curses.COLOR_YELLOW
        else:
            color = curses.COLOR_GREEN
            
        self.draw_panel(y, x, width, height, "System Resources", content)

    def draw_token_panel(self, y, x, width, height):
        """Draw token metrics panel"""
        stats = get_token_stats()
        
        content = f"""
  Today's Usage:
    Input Tokens:  {stats['input']:,}
    Output Tokens: {stats['output']:,}
    Total Tokens:  {stats['input'] + stats['output']:,}
    
  Cost Tracking:
    Daily Cost:    ${stats['cost']:.4f}
    
  Context Window:
    Usage:         {get_context_window_usage():>5.1f}% (placeholder)
        """
        
        self.draw_panel(y, x, width, height, "Token Metrics", content)

    def draw_sessions_panel(self, y, x, width, height):
        """Draw active sessions panel"""
        sessions = get_active_sessions()
        
        if sessions:
            content = "\n".join([f"  • {s}" for s in sessions])
        else:
            content = "  No active sessions"
            
        self.draw_panel(y, x, width, height, "Active Sessions", content)

    def draw_cron_panel(self, y, x, width, height):
        """Draw cron jobs panel"""
        jobs = get_cron_jobs()
        
        if jobs:
            lines = []
            for job in jobs[:4]:  # Show max 4 jobs
                status_char = '✓' if job['status'] == 'ok' else '✗'
                lines.append(f"  {status_char} {job['name'][:25]}")
                lines.append(f"    Next: {job['next']}")
            content = "\n".join(lines)
        else:
            content = "  No cron jobs configured"
            
        self.draw_panel(y, x, width, height, "Cron Jobs", content)

    def draw_activity_panel(self, y, x, width, height):
        """Draw recent activity panel"""
        # This could be enhanced to show live tool calls
        content = """
  Recent Activity:
  • Dashboard started
  • Metrics updating every 2s
  
  (Live feed coming soon)
        """
        
        self.draw_panel(y, x, width, height, "Activity Feed", content)

    def run(self):
        """Main dashboard loop"""
        try:
            while True:
                # Check for quit command
                try:
                    key = self.stdscr.getch()
                    if key == ord('q') or key == ord('Q'):
                        break
                except:
                    pass
                
                # Check if it's time to refresh
                if time.time() - self.last_refresh >= REFRESH_RATE:
                    self.stdscr.clear()
                    
                    # Get terminal size
                    height, width = self.stdscr.getmaxyx()
                    
                    # Draw header
                    self.draw_header()
                    
                    # Calculate panel sizes
                    panel_width = width // 3 - 2
                    panel_height = (height - 4) // 2
                    
                    # Draw panels in grid layout
                    self.draw_system_panel(2, 1, panel_width, panel_height, "System Resources")
                    self.draw_token_panel(2, 1 + panel_width + 2, panel_width, panel_height, "Token Metrics")
                    self.draw_sessions_panel(2 + panel_height + 1, 1, panel_width, panel_height, "Active Sessions")
                    self.draw_cron_panel(2 + panel_height + 1, 1 + panel_width + 2, panel_width, panel_height, "Cron Jobs")
                    
                    # Activity feed at bottom
                    self.draw_activity_panel(height - panel_height - 2, 1 + (panel_width + 2) * 2, 
                                           width - (panel_width + 2) * 2 - 1, panel_height, "Activity Feed")
                    
                    self.stdscr.refresh()
                    self.last_refresh = time.time()
                
                # Small sleep to prevent CPU spinning
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            pass
        finally:
            curses.endwin()
            print("\nDashboard stopped.")

def run_dashboard(stdscr):
    """Wrapper for curses"""
    dashboard = Dashboard(stdscr)
    dashboard.run()

def main():
    """Entry point"""
    print("Starting Watson Hermes Dashboard...")
    print("Press 'q' to quit\n")
    curses.wrapper(run_dashboard)

if __name__ == '__main__':
    main()
