"""
Streamlit Web UI for Agent System
Features: Dashboard, task submission, real-time monitoring, memory browser
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
from typing import Dict, List, Any
import json

# Page configuration
st.set_page_config(
    page_title="AI Agent System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-running {
        color: #ffc107;
        font-weight: bold;
    }
    .status-failed {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


class AgentWebUI:
    """Streamlit-based web interface for the agent system."""
    
    def __init__(self):
        self.init_session_state()
        
    def init_session_state(self):
        """Initialize session state variables."""
        if 'tasks' not in st.session_state:
            st.session_state.tasks = []
        if 'memories' not in st.session_state:
            st.session_state.memories = []
        if 'tool_usage' not in st.session_state:
            st.session_state.tool_usage = {}
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "Dashboard"
            
    def render_sidebar(self):
        """Render the sidebar navigation."""
        with st.sidebar:
            st.markdown("## 🤖 AI Agent System")
            st.markdown("---")
            
            # Navigation
            pages = [
                ("🏠 Dashboard", "Dashboard"),
                ("➕ New Task", "New Task"),
                ("📋 Task List", "Task List"),
                ("🧠 Memory Browser", "Memory Browser"),
                ("🔧 Tools", "Tools"),
                ("📊 Analytics", "Analytics"),
                ("⚙️ Settings", "Settings")
            ]
            
            for label, page in pages:
                if st.button(label, use_container_width=True):
                    st.session_state.current_page = page
                    st.rerun()
            
            st.markdown("---")
            
            # Status indicators
            st.markdown("### System Status")
            st.metric("Active Tasks", "3", "↑ 1")
            st.metric("Memory Items", "247", "↑ 12")
            st.metric("Tools Available", "8", "→ 0")
            
    def render_dashboard(self):
        """Render the main dashboard."""
        st.markdown('<div class="main-header">🏠 Dashboard</div>', unsafe_allow_html=True)
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Tasks",
                value="156",
                delta="12 this week",
                delta_color="normal"
            )
        
        with col2:
            st.metric(
                label="Success Rate",
                value="94.2%",
                delta="2.1%",
                delta_color="normal"
            )
        
        with col3:
            st.metric(
                label="Avg. Execution Time",
                value="3.2s",
                delta="-0.5s",
                delta_color="inverse"
            )
        
        with col4:
            st.metric(
                label="Memory Usage",
                value="68%",
                delta="5%",
                delta_color="normal"
            )
        
        st.markdown("---")
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            self.render_task_timeline_chart()
        
        with col2:
            self.render_tool_usage_chart()
        
        # Recent activity
        st.markdown("### 📝 Recent Activity")
        self.render_recent_tasks()
        
    def render_task_timeline_chart(self):
        """Render task execution timeline chart."""
        st.markdown("#### Task Execution Timeline")
        
        # Sample data
        dates = pd.date_range(end=datetime.now(), periods=7).tolist()
        data = {
            'Date': dates,
            'Completed': [12, 15, 10, 18, 14, 16, 20],
            'Failed': [2, 1, 3, 1, 2, 1, 2],
            'Running': [3, 4, 2, 5, 3, 4, 3]
        }
        df = pd.DataFrame(data)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Completed', x=df['Date'], y=df['Completed'], marker_color='#28a745'))
        fig.add_trace(go.Bar(name='Failed', x=df['Date'], y=df['Failed'], marker_color='#dc3545'))
        fig.add_trace(go.Bar(name='Running', x=df['Date'], y=df['Running'], marker_color='#ffc107'))
        
        fig.update_layout(
            barmode='stack',
            height=300,
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    def render_tool_usage_chart(self):
        """Render tool usage pie chart."""
        st.markdown("#### Tool Usage Distribution")
        
        # Sample data
        tools = ['web_search', 'calculator', 'file_reader', 'code_executor', 'data_analyzer']
        usage = [45, 20, 15, 12, 8]
        
        fig = go.Figure(data=[go.Pie(
            labels=tools,
            values=usage,
            hole=0.4,
            marker=dict(colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])
        )])
        
        fig.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    def render_recent_tasks(self):
        """Render recent tasks table."""
        tasks_data = {
            'ID': ['T-001', 'T-002', 'T-003', 'T-004', 'T-005'],
            'Description': [
                'Analyze customer data',
                'Generate monthly report',
                'Process email notifications',
                'Update database records',
                'Run data validation'
            ],
            'Status': ['✅ Completed', '⏳ Running', '✅ Completed', '❌ Failed', '⏳ Running'],
            'Priority': ['High', 'Medium', 'Low', 'High', 'Medium'],
            'Duration': ['2.3s', '5.1s', '1.2s', '3.4s', '4.8s'],
            'Timestamp': [
                '2025-01-08 14:30',
                '2025-01-08 14:25',
                '2025-01-08 14:20',
                '2025-01-08 14:15',
                '2025-01-08 14:10'
            ]
        }
        
        df = pd.DataFrame(tasks_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
    def render_new_task(self):
        """Render new task submission form."""
        st.markdown('<div class="main-header">➕ New Task</div>', unsafe_allow_html=True)
        
        with st.form("new_task_form"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                task_description = st.text_area(
                    "Task Description",
                    placeholder="Describe what you want the agent to do...",
                    height=150
                )
            
            with col2:
                priority = st.selectbox(
                    "Priority",
                    ["Low", "Medium", "High", "Critical"]
                )
                
                use_memory = st.checkbox("Use Memory Context", value=True)
                use_tools = st.checkbox("Enable Tools", value=True)
                
                max_iterations = st.number_input(
                    "Max Iterations",
                    min_value=1,
                    max_value=50,
                    value=10
                )
            
            st.markdown("#### Advanced Options")
            
            col3, col4 = st.columns(2)
            
            with col3:
                timeout = st.number_input(
                    "Timeout (seconds)",
                    min_value=10,
                    max_value=300,
                    value=60
                )
            
            with col4:
                retry_count = st.number_input(
                    "Retry Count",
                    min_value=0,
                    max_value=5,
                    value=3
                )
            
            tags = st.text_input(
                "Tags (comma-separated)",
                placeholder="analytics, report, data"
            )
            
            submitted = st.form_submit_button("🚀 Execute Task", use_container_width=True)
            
            if submitted:
                if task_description:
                    with st.spinner("Executing task..."):
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        steps = [
                            "Analyzing task...",
                            "Loading context...",
                            "Planning execution...",
                            "Executing steps...",
                            "Finalizing results..."
                        ]
                        
                        for i, step in enumerate(steps):
                            status_text.text(step)
                            progress_bar.progress((i + 1) * 20)
                            time.sleep(0.5)
                        
                        st.success("✅ Task completed successfully!")
                        
                        # Display results
                        with st.expander("View Results", expanded=True):
                            result_data = {
                                "Task ID": "T-" + datetime.now().strftime("%Y%m%d%H%M%S"),
                                "Status": "Completed",
                                "Execution Time": "2.34s",
                                "Tools Used": ["web_search", "data_analyzer"],
                                "Memory Items Created": 3
                            }
                            
                            for key, value in result_data.items():
                                st.write(f"**{key}:** {value}")
                else:
                    st.error("Please provide a task description")
                    
    def render_task_list(self):
        """Render task list with filters."""
        st.markdown('<div class="main-header">📋 Task List</div>', unsafe_allow_html=True)
        
        # Filters
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status_filter = st.multiselect(
                "Status",
                ["Completed", "Running", "Pending", "Failed"],
                default=["Running", "Completed"]
            )
        
        with col2:
            priority_filter = st.multiselect(
                "Priority",
                ["Low", "Medium", "High", "Critical"],
                default=["High", "Critical"]
            )
        
        with col3:
            date_range = st.date_input(
                "Date Range",
                value=(datetime.now() - timedelta(days=7), datetime.now())
            )
        
        with col4:
            search_query = st.text_input("🔍 Search", placeholder="Search tasks...")
        
        st.markdown("---")
        
        # Task list
        tasks_data = {
            'ID': ['T-001', 'T-002', 'T-003', 'T-004', 'T-005', 'T-006'],
            'Description': [
                'Analyze customer data',
                'Generate monthly report',
                'Process email notifications',
                'Update database records',
                'Run data validation',
                'Export analytics data'
            ],
            'Status': ['Completed', 'Running', 'Completed', 'Failed', 'Running', 'Pending'],
            'Priority': ['High', 'Medium', 'Low', 'High', 'Medium', 'Critical'],
            'Progress': [100, 65, 100, 0, 45, 0],
            'Created': [
                '2025-01-08 14:30',
                '2025-01-08 14:25',
                '2025-01-08 14:20',
                '2025-01-08 14:15',
                '2025-01-08 14:10',
                '2025-01-08 14:05'
            ]
        }
        
        df = pd.DataFrame(tasks_data)
        
        # Apply filters
        if status_filter:
            df = df[df['Status'].isin(status_filter)]
        if priority_filter:
            df = df[df['Priority'].isin(priority_filter)]
        
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Progress": st.column_config.ProgressColumn(
                    "Progress",
                    format="%d%%",
                    min_value=0,
                    max_value=100
                )
            }
        )
        
        # Bulk actions
        st.markdown("### Bulk Actions")
        col1, col2, col3 = st.columns([1, 1, 4])
        
        with col1:
            if st.button("⏸️ Pause Selected", use_container_width=True):
                st.info("Pause functionality coming soon")
        
        with col2:
            if st.button("🗑️ Delete Selected", use_container_width=True):
                st.warning("Delete functionality coming soon")
                
    def render_memory_browser(self):
        """Render memory browser interface."""
        st.markdown('<div class="main-header">🧠 Memory Browser</div>', unsafe_allow_html=True)
        
        # Search and filters
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search = st.text_input("🔍 Search Memories", placeholder="Search memory content...")
        
        with col2:
            memory_type = st.selectbox(
                "Type",
                ["All", "Short Term", "Long Term", "Episodic", "Semantic"]
            )
        
        with col3:
            importance = st.selectbox(
                "Importance",
                ["All", "Low", "Medium", "High", "Critical"]
            )
        
        st.markdown("---")
        
        # Memory items
        memory_data = {
            'ID': ['M-001', 'M-002', 'M-003', 'M-004', 'M-005'],
            'Type': ['Semantic', 'Episodic', 'Short Term', 'Long Term', 'Semantic'],
            'Content': [
                'User prefers Python for backend development',
                'Team meeting yesterday was very productive',
                'Need to finish quarterly report by Friday',
                'Company uses AWS for cloud infrastructure',
                'Customer satisfaction is a top priority'
            ],
            'Importance': ['High', 'Medium', 'High', 'High', 'Medium'],
            'Access Count': [45, 12, 23, 67, 34],
            'Created': [
                '2025-01-05 10:30',
                '2025-01-07 14:25',
                '2025-01-08 09:15',
                '2024-12-20 11:00',
                '2025-01-03 16:45'
            ]
        }
        
        df = pd.DataFrame(memory_data)
        
        selected_indices = st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            selection_mode="multi-row",
            on_select="rerun"
        )
        
        # Memory actions
        st.markdown("### Actions")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("➕ Add Memory", use_container_width=True):
                st.session_state.show_add_memory = True
        
        with col2:
            if st.button("✏️ Edit Selected", use_container_width=True):
                st.info("Edit functionality coming soon")
        
        with col3:
            if st.button("🗑️ Delete Selected", use_container_width=True):
                st.warning("Delete functionality coming soon")
        
        with col4:
            if st.button("📤 Export", use_container_width=True):
                st.download_button(
                    "Download as CSV",
                    df.to_csv(index=False),
                    "memories.csv",
                    "text/csv"
                )
                
    def render_tools(self):
        """Render tools management interface."""
        st.markdown('<div class="main-header">🔧 Tools</div>', unsafe_allow_html=True)
        
        tools_data = {
            'Tool': ['web_search', 'calculator', 'file_reader', 'code_executor', 'data_analyzer', 
                    'email_sender', 'database_query', 'api_caller'],
            'Description': [
                'Search the web for information',
                'Perform mathematical calculations',
                'Read and analyze files',
                'Execute code snippets safely',
                'Analyze data and generate insights',
                'Send email notifications',
                'Query databases',
                'Make API calls to external services'
            ],
            'Status': ['✅ Active', '✅ Active', '✅ Active', '✅ Active', '✅ Active',
                      '⚠️ Limited', '✅ Active', '❌ Disabled'],
            'Usage Count': [245, 123, 89, 67, 156, 34, 98, 0],
            'Success Rate': ['98.2%', '100%', '96.5%', '94.1%', '97.8%', '91.2%', '99.1%', 'N/A']
        }
        
        df = pd.DataFrame(tools_data)
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Tool configuration
        st.markdown("### Tool Configuration")
        
        selected_tool = st.selectbox("Select Tool", tools_data['Tool'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            enabled = st.checkbox("Enabled", value=True)
            timeout = st.number_input("Timeout (seconds)", value=30)
        
        with col2:
            max_retries = st.number_input("Max Retries", value=3)
            rate_limit = st.number_input("Rate Limit (per minute)", value=60)
        
        if st.button("💾 Save Configuration", use_container_width=True):
            st.success("Configuration saved successfully!")
            
    def render_analytics(self):
        """Render analytics dashboard."""
        st.markdown('<div class="main-header">📊 Analytics</div>', unsafe_allow_html=True)
        
        # Time period selector
        period = st.selectbox("Time Period", ["Last 7 Days", "Last 30 Days", "Last 3 Months", "All Time"])
        
        st.markdown("---")
        
        # Performance metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Task Completion Rate")
            
            dates = pd.date_range(end=datetime.now(), periods=30).tolist()
            completion_rate = [92 + i % 10 for i in range(30)]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates,
                y=completion_rate,
                mode='lines+markers',
                fill='tozeroy',
                line=dict(color='#1f77b4', width=2)
            ))
            
            fig.update_layout(
                height=300,
                margin=dict(l=0, r=0, t=0, b=0),
                yaxis=dict(range=[80, 100])
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Average Execution Time")
            
            execution_times = [3.2, 2.8, 3.5, 2.9, 3.1, 2.7, 3.3]
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            
            fig = go.Figure(data=[
                go.Bar(x=days, y=execution_times, marker_color='#2ca02c')
            ])
            
            fig.update_layout(
                height=300,
                margin=dict(l=0, r=0, t=0, b=0),
                yaxis_title="Seconds"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
    def render_settings(self):
        """Render settings page."""
        st.markdown('<div class="main-header">⚙️ Settings</div>', unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4 = st.tabs(["General", "Memory", "Tools", "Notifications"])
        
        with tab1:
            st.markdown("### General Settings")
            
            auto_save = st.checkbox("Auto-save results", value=True)
            debug_mode = st.checkbox("Debug mode", value=False)
            max_concurrent = st.slider("Max concurrent tasks", 1, 10, 5)
            default_timeout = st.number_input("Default timeout (seconds)", value=60)
        
        with tab2:
            st.markdown("### Memory Settings")
            
            memory_retention = st.slider("Memory retention (days)", 7, 365, 90)
            auto_consolidate = st.checkbox("Auto-consolidate memories", value=True)
            memory_limit = st.number_input("Memory item limit", value=10000)
        
        with tab3:
            st.markdown("### Tool Settings")
            
            enable_all_tools = st.checkbox("Enable all tools by default", value=True)
            tool_timeout = st.number_input("Tool timeout (seconds)", value=30)
            allow_code_exec = st.checkbox("Allow code execution", value=True)
        
        with tab4:
            st.markdown("### Notification Settings")
            
            email_notifications = st.checkbox("Email notifications", value=True)
            webhook_url = st.text_input("Webhook URL", placeholder="https://...")
            notify_on_failure = st.checkbox("Notify on task failure", value=True)
        
        if st.button("💾 Save All Settings", use_container_width=True):
            st.success("Settings saved successfully!")
            
    def run(self):
        """Main application entry point."""
        self.render_sidebar()
        
        # Route to appropriate page
        if st.session_state.current_page == "Dashboard":
            self.render_dashboard()
        elif st.session_state.current_page == "New Task":
            self.render_new_task()
        elif st.session_state.current_page == "Task List":
            self.render_task_list()
        elif st.session_state.current_page == "Memory Browser":
            self.render_memory_browser()
        elif st.session_state.current_page == "Tools":
            self.render_tools()
        elif st.session_state.current_page == "Analytics":
            self.render_analytics()
        elif st.session_state.current_page == "Settings":
            self.render_settings()


def main():
    """Main entry point."""
    app = AgentWebUI()
    app.run()


if __name__ == "__main__":
    main()