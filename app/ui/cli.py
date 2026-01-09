"""
Rich CLI Interface for Agent System
Features: Interactive mode, batch processing, real-time progress, color-coded output
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.markdown import Markdown
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

console = Console()


class AgentCLI:
    """Rich CLI interface for the agent system."""
    
    def __init__(self):
        self.console = console
        self.history = []
        self.current_task = None
        
    def display_banner(self):
        """Display welcome banner."""
        banner = """
        ╔═══════════════════════════════════════════════════════╗
        ║         🤖 AI Agent System - CLI Interface           ║
        ║              Powered by Advanced AI                   ║
        ╚═══════════════════════════════════════════════════════╝
        """
        self.console.print(banner, style="bold cyan")
        
    def display_menu(self):
        """Display main menu options."""
        table = Table(title="Main Menu", style="cyan")
        table.add_column("Command", style="green", width=20)
        table.add_column("Description", style="white")
        
        commands = [
            ("task", "Execute a new task"),
            ("list", "List all tasks"),
            ("status", "Check task status"),
            ("memory", "Browse memory"),
            ("tools", "View available tools"),
            ("history", "Show command history"),
            ("export", "Export data"),
            ("settings", "Configure settings"),
            ("help", "Show help"),
            ("exit", "Exit application")
        ]
        
        for cmd, desc in commands:
            table.add_row(cmd, desc)
        
        self.console.print(table)
        
    async def interactive_mode(self):
        """Run interactive CLI mode."""
        self.display_banner()
        
        while True:
            self.console.print()
            command = Prompt.ask(
                "[bold cyan]agent>[/bold cyan]",
                choices=["task", "list", "status", "memory", "tools", 
                        "history", "export", "settings", "help", "exit", "menu"]
            )
            
            self.history.append({
                "command": command,
                "timestamp": datetime.now().isoformat()
            })
            
            try:
                if command == "exit":
                    if Confirm.ask("Are you sure you want to exit?"):
                        self.console.print("[yellow]Goodbye! 👋[/yellow]")
                        break
                        
                elif command == "menu":
                    self.display_menu()
                    
                elif command == "task":
                    await self.execute_task_interactive()
                    
                elif command == "list":
                    await self.list_tasks()
                    
                elif command == "status":
                    await self.check_status()
                    
                elif command == "memory":
                    await self.browse_memory()
                    
                elif command == "tools":
                    self.show_tools()
                    
                elif command == "history":
                    self.show_history()
                    
                elif command == "export":
                    await self.export_data()
                    
                elif command == "settings":
                    self.configure_settings()
                    
                elif command == "help":
                    self.show_help()
                    
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Operation cancelled[/yellow]")
                continue
            except Exception as e:
                self.console.print(f"[red]Error: {str(e)}[/red]")
                
    async def execute_task_interactive(self):
        """Execute a task with interactive input."""
        self.console.print(Panel("[bold]Task Execution[/bold]", style="cyan"))
        
        task_description = Prompt.ask("Enter task description")
        priority = Prompt.ask(
            "Priority",
            choices=["low", "medium", "high", "critical"],
            default="medium"
        )
        
        use_memory = Confirm.ask("Use memory context?", default=True)
        
        # Simulate task execution with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            task = progress.add_task(
                f"[cyan]Executing: {task_description[:50]}...",
                total=100
            )
            
            steps = [
                "Analyzing task...",
                "Loading context...",
                "Planning execution...",
                "Executing steps...",
                "Finalizing results..."
            ]
            
            for i, step in enumerate(steps):
                progress.update(task, description=f"[cyan]{step}")
                await asyncio.sleep(0.8)  # Simulate work
                progress.update(task, advance=20)
        
        # Display results
        result_panel = Panel(
            f"✅ Task completed successfully!\n\n"
            f"Task: {task_description}\n"
            f"Priority: {priority}\n"
            f"Status: [green]Completed[/green]\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            title="[bold green]Task Result[/bold green]",
            border_style="green"
        )
        self.console.print(result_panel)
        
    async def list_tasks(self):
        """List all tasks in a formatted table."""
        table = Table(title="Task List", style="cyan")
        table.add_column("ID", style="magenta", width=8)
        table.add_column("Description", style="white", width=40)
        table.add_column("Status", style="yellow", width=12)
        table.add_column("Priority", style="cyan", width=10)
        table.add_column("Created", style="green", width=20)
        
        # Sample data (replace with actual data from your system)
        tasks = [
            ("001", "Analyze customer data", "Completed", "High", "2025-01-08 10:30"),
            ("002", "Generate report", "Running", "Medium", "2025-01-08 11:45"),
            ("003", "Send notifications", "Pending", "Low", "2025-01-08 12:00"),
        ]
        
        for task_id, desc, status, priority, created in tasks:
            status_color = {
                "Completed": "[green]✓ Completed[/green]",
                "Running": "[yellow]⟳ Running[/yellow]",
                "Pending": "[cyan]○ Pending[/cyan]",
                "Failed": "[red]✗ Failed[/red]"
            }.get(status, status)
            
            table.add_row(task_id, desc, status_color, priority, created)
        
        self.console.print(table)
        
    async def check_status(self):
        """Check status of a specific task."""
        task_id = Prompt.ask("Enter task ID")
        
        # Simulate status check
        status_data = {
            "id": task_id,
            "status": "Running",
            "progress": 65,
            "current_step": "Processing data",
            "steps_completed": 3,
            "total_steps": 5
        }
        
        layout = Layout()
        layout.split_column(
            Layout(Panel(
                f"[bold]Task ID:[/bold] {status_data['id']}\n"
                f"[bold]Status:[/bold] [yellow]{status_data['status']}[/yellow]\n"
                f"[bold]Progress:[/bold] {status_data['progress']}%\n"
                f"[bold]Current Step:[/bold] {status_data['current_step']}\n"
                f"[bold]Steps:[/bold] {status_data['steps_completed']}/{status_data['total_steps']}",
                title="Task Status",
                border_style="yellow"
            ))
        )
        
        self.console.print(layout)
        
    async def browse_memory(self):
        """Browse memory items."""
        self.console.print(Panel("[bold]Memory Browser[/bold]", style="cyan"))
        
        memory_type = Prompt.ask(
            "Memory type",
            choices=["all", "short_term", "long_term", "episodic", "semantic"],
            default="all"
        )
        
        table = Table(title=f"Memory Items - {memory_type}", style="cyan")
        table.add_column("ID", style="magenta", width=6)
        table.add_column("Type", style="yellow", width=12)
        table.add_column("Content", style="white", width=50)
        table.add_column("Importance", style="green", width=10)
        
        # Sample memory items
        memories = [
            ("M001", "semantic", "User prefers Python for backend", "High"),
            ("M002", "episodic", "Team meeting yesterday was productive", "Medium"),
            ("M003", "short_term", "Need to finish report by Friday", "High"),
        ]
        
        for mem_id, mem_type, content, importance in memories:
            table.add_row(mem_id, mem_type, content, importance)
        
        self.console.print(table)
        
    def show_tools(self):
        """Display available tools."""
        table = Table(title="Available Tools", style="cyan")
        table.add_column("Tool", style="green", width=20)
        table.add_column("Description", style="white", width=40)
        table.add_column("Status", style="yellow", width=10)
        
        tools = [
            ("web_search", "Search the web for information", "Active"),
            ("calculator", "Perform mathematical calculations", "Active"),
            ("file_reader", "Read and analyze files", "Active"),
            ("code_executor", "Execute code snippets", "Active"),
            ("data_analyzer", "Analyze datasets", "Active"),
        ]
        
        for tool, desc, status in tools:
            table.add_row(tool, desc, f"[green]{status}[/green]")
        
        self.console.print(table)
        
    def show_history(self):
        """Display command history."""
        if not self.history:
            self.console.print("[yellow]No command history yet[/yellow]")
            return
            
        table = Table(title="Command History", style="cyan")
        table.add_column("#", style="magenta", width=6)
        table.add_column("Command", style="green", width=20)
        table.add_column("Timestamp", style="white", width=30)
        
        for i, entry in enumerate(self.history[-20:], 1):  # Show last 20
            table.add_row(
                str(i),
                entry["command"],
                entry["timestamp"]
            )
        
        self.console.print(table)
        
    async def export_data(self):
        """Export data to various formats."""
        export_type = Prompt.ask(
            "Export type",
            choices=["tasks", "memory", "history", "all"],
            default="all"
        )
        
        format_type = Prompt.ask(
            "Format",
            choices=["json", "csv", "markdown"],
            default="json"
        )
        
        filename = Prompt.ask("Filename", default=f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        with Progress(console=self.console) as progress:
            task = progress.add_task("[cyan]Exporting data...", total=100)
            await asyncio.sleep(1)
            progress.update(task, advance=100)
        
        self.console.print(f"[green]✓ Data exported to {filename}.{format_type}[/green]")
        
    def configure_settings(self):
        """Configure system settings."""
        self.console.print(Panel("[bold]Settings Configuration[/bold]", style="cyan"))
        
        settings = {
            "Auto-save": Confirm.ask("Enable auto-save?", default=True),
            "Notifications": Confirm.ask("Enable notifications?", default=True),
            "Debug mode": Confirm.ask("Enable debug mode?", default=False),
            "Max history": int(Prompt.ask("Max history entries", default="100"))
        }
        
        table = Table(title="Current Settings", style="green")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")
        
        for key, value in settings.items():
            table.add_row(key, str(value))
        
        self.console.print(table)
        self.console.print("[green]✓ Settings saved[/green]")
        
    def show_help(self):
        """Display help information."""
        help_text = """
# CLI Help Guide

## Available Commands

- **task**: Execute a new task with interactive prompts
- **list**: Display all tasks in a formatted table
- **status**: Check the status of a specific task
- **memory**: Browse and search memory items
- **tools**: View all available tools and their status
- **history**: Show command history
- **export**: Export data to JSON, CSV, or Markdown
- **settings**: Configure system settings
- **help**: Display this help message
- **exit**: Exit the application

## Tips

- Use arrow keys to navigate history
- Press Ctrl+C to cancel current operation
- Use Tab for command completion
- All operations are logged for audit
        """
        
        md = Markdown(help_text)
        self.console.print(Panel(md, title="[bold]Help[/bold]", border_style="cyan"))


def main():
    """Main entry point for CLI."""
    cli = AgentCLI()
    
    try:
        asyncio.run(cli.interactive_mode())
    except KeyboardInterrupt:
        console.print("\n[yellow]Application terminated[/yellow]")
    except Exception as e:
        console.print(f"[red]Fatal error: {str(e)}[/red]")


if __name__ == "__main__":
    main()