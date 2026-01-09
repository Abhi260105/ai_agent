"""
Progress Bar Component - Visualize task progress
"""

from rich.progress import (
    Progress, 
    SpinnerColumn, 
    TextColumn, 
    BarColumn, 
    TimeElapsedColumn,
    TimeRemainingColumn,
    TaskProgressColumn
)
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
import streamlit as st
import time
from typing import Optional, Callable
from datetime import datetime


class ProgressBar:
    """Enhanced progress bar for visualizing task execution."""
    
    def __init__(self, total: int = 100, description: str = "Processing"):
        """
        Initialize progress bar.
        
        Args:
            total: Total number of steps
            description: Description of the task
        """
        self.total = total
        self.description = description
        self.current = 0
        self.start_time = None
        self.end_time = None
        
    def create_rich_progress(self) -> Progress:
        """Create a Rich progress bar with multiple columns."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="green", finished_style="bold green"),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=Console()
        )
        
    def start_cli(self, console: Optional[Console] = None):
        """
        Start CLI progress tracking.
        
        Args:
            console: Rich console instance
        """
        if console is None:
            console = Console()
            
        self.start_time = datetime.now()
        
        with self.create_rich_progress() as progress:
            task_id = progress.add_task(
                f"[cyan]{self.description}",
                total=self.total
            )
            
            return progress, task_id
            
    def update_cli(self, progress: Progress, task_id: int, advance: int = 1, description: Optional[str] = None):
        """
        Update CLI progress.
        
        Args:
            progress: Rich Progress instance
            task_id: Task ID
            advance: Amount to advance
            description: Optional new description
        """
        if description:
            progress.update(task_id, description=f"[cyan]{description}")
        progress.update(task_id, advance=advance)
        
    def render_streamlit(self, current: Optional[int] = None, text: Optional[str] = None):
        """
        Render progress bar in Streamlit.
        
        Args:
            current: Current progress value
            text: Optional text to display
        """
        if current is not None:
            self.current = current
            
        progress_pct = self.current / self.total if self.total > 0 else 0
        
        # Display text
        if text:
            st.markdown(f"**{text}**")
        else:
            st.markdown(f"**{self.description}**")
        
        # Progress bar
        st.progress(progress_pct, text=f"{int(progress_pct * 100)}% Complete")
        
        # Additional info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current", f"{self.current}/{self.total}")
        with col2:
            if self.start_time:
                elapsed = (datetime.now() - self.start_time).total_seconds()
                st.metric("Elapsed", f"{elapsed:.1f}s")
        with col3:
            if self.start_time and progress_pct > 0:
                elapsed = (datetime.now() - self.start_time).total_seconds()
                estimated_total = elapsed / progress_pct
                remaining = estimated_total - elapsed
                st.metric("Remaining", f"{remaining:.1f}s")
                
    def render_multi_step_streamlit(self, steps: list, current_step: int):
        """
        Render multi-step progress in Streamlit.
        
        Args:
            steps: List of step names
            current_step: Current step index (0-based)
        """
        st.markdown("### Execution Steps")
        
        for i, step in enumerate(steps):
            if i < current_step:
                # Completed
                st.markdown(f"✅ **{step}**")
            elif i == current_step:
                # Current
                st.markdown(f"🔄 **{step}** (In Progress)")
                st.progress(0.5, text="Processing...")
            else:
                # Pending
                st.markdown(f"⏳ {step}")
                
    @staticmethod
    def create_multi_task_progress() -> Progress:
        """Create progress tracker for multiple tasks."""
        return Progress(
            TextColumn("[bold blue]{task.fields[name]}", justify="left"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=Console()
        )
        
    @staticmethod
    def render_comparison_streamlit(tasks: list):
        """
        Render comparison of multiple task progress bars.
        
        Args:
            tasks: List of task dictionaries with 'name' and 'progress'
        """
        st.markdown("### Task Progress Comparison")
        
        for task in tasks:
            name = task.get('name', 'Unknown')
            progress = task.get('progress', 0)
            status = task.get('status', 'running')
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{name}**")
                st.progress(progress / 100, text=f"{progress}%")
            
            with col2:
                status_emoji = {
                    'completed': '✅',
                    'running': '🔄',
                    'pending': '⏳',
                    'failed': '❌'
                }.get(status, '❓')
                st.markdown(f"### {status_emoji}")
                
    @staticmethod
    def animated_progress_cli(console: Console, steps: list, delay: float = 0.5):
        """
        Display animated progress through multiple steps in CLI.
        
        Args:
            console: Rich console instance
            steps: List of step names
            delay: Delay between steps in seconds
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task(
                "[cyan]Starting...",
                total=len(steps)
            )
            
            for i, step in enumerate(steps):
                progress.update(
                    task,
                    description=f"[cyan]{step}",
                    advance=1
                )
                time.sleep(delay)
                
    @staticmethod
    def render_detailed_progress_panel(
        console: Console,
        task_name: str,
        current_step: str,
        progress_pct: int,
        steps_completed: int,
        total_steps: int,
        elapsed_time: float
    ):
        """
        Render detailed progress panel in CLI.
        
        Args:
            console: Rich console instance
            task_name: Name of the task
            current_step: Current step description
            progress_pct: Progress percentage
            steps_completed: Number of completed steps
            total_steps: Total number of steps
            elapsed_time: Elapsed time in seconds
        """
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="bold cyan")
        table.add_column(style="white")
        
        table.add_row("Task:", task_name)
        table.add_row("Current Step:", current_step)
        table.add_row("Progress:", f"{progress_pct}%")
        table.add_row("Steps:", f"{steps_completed}/{total_steps}")
        table.add_row("Elapsed Time:", f"{elapsed_time:.2f}s")
        
        # Progress bar
        bar_length = 30
        filled = int(bar_length * progress_pct / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        table.add_row("", f"[green]{bar}[/green]")
        
        panel = Panel(
            table,
            title="[bold]Task Progress[/bold]",
            border_style="cyan",
            padding=(1, 2)
        )
        
        console.print(panel)


class LiveProgressTracker:
    """Real-time progress tracker with live updates."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize live progress tracker."""
        self.console = console or Console()
        self.tasks = {}
        self.start_time = datetime.now()
        
    def add_task(self, task_id: str, description: str, total: int):
        """Add a task to track."""
        self.tasks[task_id] = {
            'description': description,
            'total': total,
            'current': 0,
            'status': 'running'
        }
        
    def update_task(self, task_id: str, advance: int = 1, status: Optional[str] = None):
        """Update task progress."""
        if task_id in self.tasks:
            self.tasks[task_id]['current'] += advance
            if status:
                self.tasks[task_id]['status'] = status
                
    def render_live(self):
        """Render live progress updates."""
        table = Table(title="Live Progress", show_header=True)
        table.add_column("Task", style="cyan")
        table.add_column("Progress", style="green")
        table.add_column("Status", style="yellow")
        
        for task_id, task_data in self.tasks.items():
            progress_pct = (task_data['current'] / task_data['total']) * 100
            bar_length = 20
            filled = int(bar_length * progress_pct / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            status_emoji = {
                'running': '🔄',
                'completed': '✅',
                'failed': '❌',
                'paused': '⏸️'
            }.get(task_data['status'], '❓')
            
            table.add_row(
                task_data['description'],
                f"{bar} {progress_pct:.0f}%",
                f"{status_emoji} {task_data['status']}"
            )
        
        return Panel(table, title="[bold]Real-time Progress[/bold]", border_style="cyan")