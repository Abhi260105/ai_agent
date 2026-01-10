"""
Tool Monitor Component - Display tool usage and statistics
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.bar import Bar
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict


class ToolMonitor:
    """Component for monitoring tool usage and performance."""
    
    def __init__(self, tool_data: List[Dict[str, Any]]):
        """
        Initialize tool monitor.
        
        Args:
            tool_data: List of tool usage records
        """
        self.tool_data = tool_data
        self.stats = self._calculate_stats()
        
    def _calculate_stats(self) -> Dict[str, Any]:
        """Calculate tool usage statistics."""
        stats = {
            'total_calls': len(self.tool_data),
            'by_tool': defaultdict(int),
            'by_status': defaultdict(int),
            'total_duration': 0,
            'avg_duration': 0,
            'success_rate': 0
        }
        
        for record in self.tool_data:
            tool_name = record.get('tool_name', 'unknown')
            status = record.get('status', 'unknown')
            duration = record.get('duration', 0)
            
            stats['by_tool'][tool_name] += 1
            stats['by_status'][status] += 1
            stats['total_duration'] += duration
        
        if stats['total_calls'] > 0:
            stats['avg_duration'] = stats['total_duration'] / stats['total_calls']
            successful = stats['by_status'].get('success', 0)
            stats['success_rate'] = (successful / stats['total_calls']) * 100
        
        return stats
        
    def render_cli(self, console: Console):
        """
        Render tool monitor in CLI.
        
        Args:
            console: Rich console instance
        """
        # Summary panel
        summary = Panel(
            f"[bold cyan]Total Calls:[/bold cyan] {self.stats['total_calls']}\n"
            f"[bold green]Success Rate:[/bold green] {self.stats['success_rate']:.1f}%\n"
            f"[bold yellow]Avg Duration:[/bold yellow] {self.stats['avg_duration']:.2f}s",
            title="[bold]Tool Usage Summary[/bold]",
            border_style="cyan",
            padding=(1, 2)
        )
        console.print(summary)
        console.print()
        
        # Tool usage table
        self._render_tool_table_cli(console)
        console.print()
        
        # Recent activity
        self._render_recent_activity_cli(console)
        
    def _render_tool_table_cli(self, console: Console):
        """Render tool usage table in CLI."""
        table = Table(title="Tool Usage Statistics", show_header=True, header_style="bold magenta")
        
        table.add_column("Tool", style="cyan", width=20)
        table.add_column("Calls", style="yellow", width=10)
        table.add_column("Success", style="green", width=10)
        table.add_column("Failed", style="red", width=10)
        table.add_column("Avg Time", style="blue", width=12)
        
        # Aggregate data by tool
        tool_stats = defaultdict(lambda: {'calls': 0, 'success': 0, 'failed': 0, 'total_time': 0})
        
        for record in self.tool_data:
            tool_name = record.get('tool_name', 'unknown')
            status = record.get('status', 'unknown')
            duration = record.get('duration', 0)
            
            tool_stats[tool_name]['calls'] += 1
            tool_stats[tool_name]['total_time'] += duration
            
            if status == 'success':
                tool_stats[tool_name]['success'] += 1
            else:
                tool_stats[tool_name]['failed'] += 1
        
        # Add rows
        for tool_name, stats in sorted(tool_stats.items(), key=lambda x: x[1]['calls'], reverse=True):
            avg_time = stats['total_time'] / stats['calls'] if stats['calls'] > 0 else 0
            
            table.add_row(
                tool_name,
                str(stats['calls']),
                str(stats['success']),
                str(stats['failed']),
                f"{avg_time:.2f}s"
            )
        
        console.print(table)
        
    def _render_recent_activity_cli(self, console: Console):
        """Render recent tool activity in CLI."""
        table = Table(title="Recent Tool Activity", show_header=True, header_style="bold magenta")
        
        table.add_column("Time", style="dim", width=20)
        table.add_column("Tool", style="cyan", width=20)
        table.add_column("Status", style="yellow", width=12)
        table.add_column("Duration", style="green", width=12)
        
        # Get last 10 records
        recent = sorted(
            self.tool_data,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )[:10]
        
        for record in recent:
            status = record.get('status', 'unknown')
            status_emoji = '✓' if status == 'success' else '✗'
            status_color = 'green' if status == 'success' else 'red'
            
            table.add_row(
                record.get('timestamp', 'N/A'),
                record.get('tool_name', 'unknown'),
                f"[{status_color}]{status_emoji} {status}[/{status_color}]",
                f"{record.get('duration', 0):.2f}s"
            )
        
        console.print(table)
        
    def render_streamlit(self):
        """Render tool monitor in Streamlit."""
        st.markdown("### 🔧 Tool Usage Monitor")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Calls", self.stats['total_calls'])
        with col2:
            st.metric("Success Rate", f"{self.stats['success_rate']:.1f}%")
        with col3:
            st.metric("Avg Duration", f"{self.stats['avg_duration']:.2f}s")
        with col4:
            unique_tools = len(self.stats['by_tool'])
            st.metric("Active Tools", unique_tools)
        
        st.markdown("---")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_tool_usage_chart_streamlit()
        
        with col2:
            self._render_status_distribution_streamlit()
        
        st.markdown("---")
        
        # Detailed table
        self._render_tool_table_streamlit()
        
        st.markdown("---")
        
        # Recent activity
        self._render_recent_activity_streamlit()
        
    def _render_tool_usage_chart_streamlit(self):
        """Render tool usage bar chart in Streamlit."""
        st.markdown("#### Tool Usage Distribution")
        
        tool_names = list(self.stats['by_tool'].keys())
        tool_counts = list(self.stats['by_tool'].values())
        
        fig = go.Figure(data=[
            go.Bar(
                x=tool_names,
                y=tool_counts,
                marker_color='#1f77b4',
                text=tool_counts,
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            xaxis_title="Tool",
            yaxis_title="Number of Calls",
            height=300,
            margin=dict(l=0, r=0, t=20, b=0),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    def _render_status_distribution_streamlit(self):
        """Render status distribution pie chart in Streamlit."""
        st.markdown("#### Status Distribution")
        
        statuses = list(self.stats['by_status'].keys())
        counts = list(self.stats['by_status'].values())
        
        colors = {
            'success': '#28a745',
            'failed': '#dc3545',
            'timeout': '#ffc107',
            'error': '#fd7e14'
        }
        
        color_list = [colors.get(status, '#6c757d') for status in statuses]
        
        fig = go.Figure(data=[go.Pie(
            labels=statuses,
            values=counts,
            marker=dict(colors=color_list),
            hole=0.4
        )])
        
        fig.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=20, b=0),
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    def _render_tool_table_streamlit(self):
        """Render detailed tool statistics table in Streamlit."""
        st.markdown("#### Tool Statistics")
        
        # Aggregate data
        tool_stats = defaultdict(lambda: {
            'calls': 0,
            'success': 0,
            'failed': 0,
            'total_time': 0,
            'min_time': float('inf'),
            'max_time': 0
        })
        
        for record in self.tool_data:
            tool_name = record.get('tool_name', 'unknown')
            status = record.get('status', 'unknown')
            duration = record.get('duration', 0)
            
            tool_stats[tool_name]['calls'] += 1
            tool_stats[tool_name]['total_time'] += duration
            tool_stats[tool_name]['min_time'] = min(tool_stats[tool_name]['min_time'], duration)
            tool_stats[tool_name]['max_time'] = max(tool_stats[tool_name]['max_time'], duration)
            
            if status == 'success':
                tool_stats[tool_name]['success'] += 1
            else:
                tool_stats[tool_name]['failed'] += 1
        
        # Build dataframe
        df_data = []
        for tool_name, stats in tool_stats.items():
            avg_time = stats['total_time'] / stats['calls'] if stats['calls'] > 0 else 0
            success_rate = (stats['success'] / stats['calls'] * 100) if stats['calls'] > 0 else 0
            
            df_data.append({
                'Tool': tool_name,
                'Total Calls': stats['calls'],
                'Success': stats['success'],
                'Failed': stats['failed'],
                'Success Rate (%)': round(success_rate, 1),
                'Avg Time (s)': round(avg_time, 2),
                'Min Time (s)': round(stats['min_time'], 2) if stats['min_time'] != float('inf') else 0,
                'Max Time (s)': round(stats['max_time'], 2)
            })
        
        df = pd.DataFrame(df_data)
        df = df.sort_values('Total Calls', ascending=False)
        
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Success Rate (%)": st.column_config.ProgressColumn(
                    "Success Rate (%)",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100
                )
            }
        )
        
    def _render_recent_activity_streamlit(self):
        """Render recent tool activity in Streamlit."""
        st.markdown("#### Recent Activity")
        
        # Get last 20 records
        recent = sorted(
            self.tool_data,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )[:20]
        
        df_data = []
        for record in recent:
            status = record.get('status', 'unknown')
            status_emoji = '✅' if status == 'success' else '❌'
            
            df_data.append({
                'Time': record.get('timestamp', 'N/A'),
                'Tool': record.get('tool_name', 'unknown'),
                'Status': f"{status_emoji} {status}",
                'Duration (s)': round(record.get('duration', 0), 2),
                'Input': str(record.get('input', ''))[:50] + '...'
            })
        
        df = pd.DataFrame(df_data)
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
    @staticmethod
    def render_live_monitor_cli(console: Console, tool_data: List[Dict], refresh_rate: int = 2):
        """
        Render live tool monitor with auto-refresh in CLI.
        
        Args:
            console: Rich console instance
            tool_data: List of tool usage records (updated externally)
            refresh_rate: Refresh rate in seconds
        """
        with Live(console=console, refresh_per_second=1/refresh_rate) as live:
            while True:
                monitor = ToolMonitor(tool_data)
                
                layout = Layout()
                layout.split_column(
                    Layout(name="summary", size=5),
                    Layout(name="table", size=15),
                    Layout(name="activity", size=12)
                )
                
                # Summary
                summary_text = (
                    f"[bold cyan]Total Calls:[/bold cyan] {monitor.stats['total_calls']}  "
                    f"[bold green]Success Rate:[/bold green] {monitor.stats['success_rate']:.1f}%  "
                    f"[bold yellow]Avg Duration:[/bold yellow] {monitor.stats['avg_duration']:.2f}s"
                )
                layout["summary"].update(Panel(summary_text, title="Live Tool Monitor", border_style="cyan"))
                
                # Tool table
                tool_table = Table(show_header=True, header_style="bold magenta")
                tool_table.add_column("Tool", style="cyan")
                tool_table.add_column("Calls", style="yellow")
                tool_table.add_column("Success Rate", style="green")
                
                for tool_name, count in monitor.stats['by_tool'].items():
                    tool_table.add_row(tool_name, str(count), "N/A")
                
                layout["table"].update(tool_table)
                
                # Recent activity
                activity_table = Table(show_header=True, header_style="bold magenta")
                activity_table.add_column("Time", style="dim")
                activity_table.add_column("Tool", style="cyan")
                activity_table.add_column("Status", style="yellow")
                
                recent = tool_data[-5:]
                for record in reversed(recent):
                    activity_table.add_row(
                        record.get('timestamp', 'N/A')[-8:],
                        record.get('tool_name', 'unknown'),
                        record.get('status', 'unknown')
                    )
                
                layout["activity"].update(Panel(activity_table, title="Recent Activity"))
                
                live.update(layout)