"""
Memory Viewer Component - Inspect and browse memory items
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.syntax import Syntax
from rich.text import Text
import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


class MemoryViewer:
    """Component for viewing and inspecting memory items."""
    
    def __init__(self, memories: List[Dict[str, Any]]):
        """
        Initialize memory viewer.
        
        Args:
            memories: List of memory dictionaries
        """
        self.memories = memories
        
    def render_cli(self, console: Console, detailed: bool = False):
        """
        Render memory viewer in CLI.
        
        Args:
            console: Rich console instance
            detailed: Show detailed view
        """
        if detailed:
            self._render_detailed_cli(console)
        else:
            self._render_list_cli(console)
            
    def _render_list_cli(self, console: Console):
        """Render memory list in CLI."""
        table = Table(title="Memory Items", show_header=True, header_style="bold magenta")
        
        table.add_column("ID", style="cyan", width=8)
        table.add_column("Type", style="yellow", width=12)
        table.add_column("Content", style="white", width=50)
        table.add_column("Importance", style="green", width=10)
        table.add_column("Access", style="dim", width=8)
        
        for memory in self.memories:
            mem_id = str(memory.get('id', 'N/A'))
            mem_type = memory.get('memory_type', 'unknown')
            content = memory.get('content', '')[:47] + "..." if len(memory.get('content', '')) > 50 else memory.get('content', '')
            importance = memory.get('importance', 'medium')
            access_count = str(memory.get('access_count', 0))
            
            # Color code importance
            importance_style = {
                'low': 'dim',
                'medium': 'yellow',
                'high': 'red',
                'critical': 'bold red'
            }.get(importance.lower(), 'white')
            
            table.add_row(
                mem_id,
                mem_type,
                content,
                Text(importance.upper(), style=importance_style),
                access_count
            )
        
        console.print(table)
        
    def _render_detailed_cli(self, console: Console):
        """Render detailed memory view in CLI."""
        for i, memory in enumerate(self.memories):
            if i > 0:
                console.print()
            
            # Build content
            content = []
            content.append(f"[bold cyan]ID:[/bold cyan] {memory.get('id', 'N/A')}")
            content.append(f"[bold cyan]Type:[/bold cyan] {memory.get('memory_type', 'unknown')}")
            content.append(f"[bold cyan]Importance:[/bold cyan] {memory.get('importance', 'medium')}")
            content.append(f"\n[bold]Content:[/bold]\n{memory.get('content', '')}")
            
            # Tags
            tags = memory.get('tags', [])
            if tags:
                content.append(f"\n[bold]Tags:[/bold] {', '.join(tags)}")
            
            # Metadata
            metadata = memory.get('metadata', {})
            if metadata:
                content.append(f"\n[bold]Metadata:[/bold]")
                for key, value in metadata.items():
                    content.append(f"  {key}: {value}")
            
            # Stats
            content.append(f"\n[dim]Access Count: {memory.get('access_count', 0)}[/dim]")
            content.append(f"[dim]Created: {memory.get('created_at', 'N/A')}[/dim]")
            
            panel = Panel(
                "\n".join(content),
                title=f"[bold]Memory: {memory.get('id', 'N/A')}[/bold]",
                border_style="cyan",
                padding=(1, 2)
            )
            
            console.print(panel)
            
    def render_streamlit(self, view_mode: str = "cards"):
        """
        Render memory viewer in Streamlit.
        
        Args:
            view_mode: Display mode - 'cards', 'table', or 'detailed'
        """
        if view_mode == "cards":
            self._render_cards_streamlit()
        elif view_mode == "table":
            self._render_table_streamlit()
        elif view_mode == "detailed":
            self._render_detailed_streamlit()
            
    def _render_cards_streamlit(self):
        """Render memories as cards in Streamlit."""
        for memory in self.memories:
            mem_type = memory.get('memory_type', 'unknown')
            importance = memory.get('importance', 'medium')
            
            # Color based on importance
            border_colors = {
                'low': '#17a2b8',
                'medium': '#ffc107',
                'high': '#fd7e14',
                'critical': '#dc3545'
            }
            border_color = border_colors.get(importance.lower(), '#6c757d')
            
            # Render card
            with st.container():
                st.markdown(f"""
                <div style="
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 16px;
                    margin: 12px 0;
                    background-color: #f8f9fa;
                    border-left: 4px solid {border_color};
                ">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="
                            background-color: #e9ecef;
                            padding: 4px 8px;
                            border-radius: 4px;
                            font-size: 12px;
                            font-weight: bold;
                            color: #495057;
                        ">{mem_type.upper()}</span>
                        <span style="
                            background-color: {border_color};
                            color: white;
                            padding: 4px 8px;
                            border-radius: 4px;
                            font-size: 12px;
                            font-weight: bold;
                        ">{importance.upper()}</span>
                    </div>
                    
                    <p style="margin: 12px 0; color: #333; line-height: 1.6;">
                        {memory.get('content', '')}
                    </p>
                    
                    <div style="display: flex; gap: 16px; font-size: 12px; color: #666; margin-top: 12px;">
                        <span>🔍 Accessed: {memory.get('access_count', 0)} times</span>
                        <span>📅 {memory.get('created_at', 'N/A')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Expandable details
                with st.expander("View Details"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**ID:**", memory.get('id', 'N/A'))
                        st.write("**Type:**", mem_type)
                        st.write("**Importance:**", importance)
                    with col2:
                        st.write("**Access Count:**", memory.get('access_count', 0))
                        st.write("**Created:**", memory.get('created_at', 'N/A'))
                    
                    tags = memory.get('tags', [])
                    if tags:
                        st.write("**Tags:**", ", ".join(tags))
                    
                    metadata = memory.get('metadata', {})
                    if metadata:
                        st.write("**Metadata:**")
                        st.json(metadata)
                        
    def _render_table_streamlit(self):
        """Render memories as a table in Streamlit."""
        df_data = []
        for memory in self.memories:
            df_data.append({
                'ID': memory.get('id', 'N/A'),
                'Type': memory.get('memory_type', 'unknown'),
                'Content': memory.get('content', '')[:50] + "...",
                'Importance': memory.get('importance', 'medium'),
                'Access Count': memory.get('access_count', 0),
                'Created': memory.get('created_at', 'N/A')
            })
        
        df = pd.DataFrame(df_data)
        
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Content": st.column_config.TextColumn(
                    "Content",
                    width="large"
                ),
                "Importance": st.column_config.TextColumn(
                    "Importance",
                    width="small"
                )
            }
        )
        
    def _render_detailed_streamlit(self):
        """Render detailed memory view in Streamlit."""
        for memory in self.memories:
            with st.expander(f"Memory: {memory.get('id', 'N/A')} - {memory.get('content', '')[:50]}..."):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Type", memory.get('memory_type', 'unknown'))
                with col2:
                    st.metric("Importance", memory.get('importance', 'medium'))
                with col3:
                    st.metric("Access Count", memory.get('access_count', 0))
                
                st.markdown("---")
                st.markdown("### Content")
                st.write(memory.get('content', ''))
                
                tags = memory.get('tags', [])
                if tags:
                    st.markdown("### Tags")
                    for tag in tags:
                        st.markdown(f"- `{tag}`")
                
                metadata = memory.get('metadata', {})
                if metadata:
                    st.markdown("### Metadata")
                    st.json(metadata)
                
                st.markdown("---")
                st.caption(f"Created: {memory.get('created_at', 'N/A')}")
                
    @staticmethod
    def render_memory_graph_cli(console: Console, memories: List[Dict], relationships: Dict):
        """
        Render memory relationships as a tree in CLI.
        
        Args:
            console: Rich console instance
            memories: List of memory items
            relationships: Dictionary of memory relationships
        """
        tree = Tree("🧠 Memory Graph", style="bold cyan")
        
        # Group by type
        memory_by_type = {}
        for memory in memories:
            mem_type = memory.get('memory_type', 'unknown')
            if mem_type not in memory_by_type:
                memory_by_type[mem_type] = []
            memory_by_type[mem_type].append(memory)
        
        # Build tree
        for mem_type, mems in memory_by_type.items():
            type_branch = tree.add(f"[yellow]{mem_type.upper()}[/yellow] ({len(mems)} items)")
            
            for memory in mems[:5]:  # Limit to 5 per type
                content = memory.get('content', '')[:40]
                mem_id = memory.get('id', 'N/A')
                importance = memory.get('importance', 'medium')
                
                mem_branch = type_branch.add(
                    f"[cyan]{mem_id}[/cyan]: {content}... [{importance}]"
                )
                
                # Add related memories
                related = relationships.get(str(mem_id), [])
                if related:
                    for rel_id in related[:3]:  # Limit to 3 related
                        mem_branch.add(f"[dim]→ Related: {rel_id}[/dim]")
        
        console.print(tree)
        
    @staticmethod
    def render_memory_timeline_streamlit(memories: List[Dict]):
        """
        Render memory timeline in Streamlit.
        
        Args:
            memories: List of memory items
        """
        st.markdown("### Memory Timeline")
        
        # Sort by date
        sorted_memories = sorted(
            memories,
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )
        
        for memory in sorted_memories:
            created_at = memory.get('created_at', 'N/A')
            mem_type = memory.get('memory_type', 'unknown')
            content = memory.get('content', '')
            
            col1, col2 = st.columns([1, 5])
            
            with col1:
                st.markdown(f"**{created_at}**")
                st.caption(mem_type)
            
            with col2:
                st.markdown(f"_{content}_")
            
            st.markdown("---")
            
    @staticmethod
    def filter_memories(
        memories: List[Dict],
        memory_type: Optional[str] = None,
        importance: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search_query: Optional[str] = None
    ) -> List[Dict]:
        """
        Filter memories based on criteria.
        
        Args:
            memories: List of memory items
            memory_type: Filter by memory type
            importance: Filter by importance level
            tags: Filter by tags
            search_query: Search in content
            
        Returns:
            Filtered list of memories
        """
        filtered = memories
        
        if memory_type:
            filtered = [m for m in filtered if m.get('memory_type') == memory_type]
        
        if importance:
            filtered = [m for m in filtered if m.get('importance') == importance]
        
        if tags:
            filtered = [
                m for m in filtered 
                if any(tag in m.get('tags', []) for tag in tags)
            ]
        
        if search_query:
            query_lower = search_query.lower()
            filtered = [
                m for m in filtered 
                if query_lower in m.get('content', '').lower()
            ]
        
        return filtered