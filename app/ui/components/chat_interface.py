"""
Chat Interface Component - Conversational UI for agent interaction
"""

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.live import Live
from rich.spinner import Spinner
import streamlit as st
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import time


class ChatInterface:
    """Conversational interface for interacting with the agent."""
    
    def __init__(self):
        """Initialize chat interface."""
        self.messages = []
        self.conversation_id = None
        
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Add a message to the conversation.
        
        Args:
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            metadata: Additional metadata
        """
        self.messages.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        })
        
    def render_cli(self, console: Console, on_input: Optional[Callable] = None):
        """
        Render chat interface in CLI.
        
        Args:
            console: Rich console instance
            on_input: Callback function for user input
        """
        console.print(Panel(
            "[bold cyan]Chat with Agent[/bold cyan]\n"
            "Type your message or 'exit' to quit.",
            border_style="cyan"
        ))
        console.print()
        
        # Display existing messages
        for msg in self.messages:
            self._render_message_cli(console, msg)
        
        # Input loop
        while True:
            user_input = Prompt.ask("\n[bold green]You[/bold green]")
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                console.print("[yellow]Ending conversation. Goodbye![/yellow]")
                break
            
            # Add user message
            self.add_message('user', user_input)
            
            # Call input handler
            if on_input:
                with console.status("[bold yellow]Agent is thinking...", spinner="dots"):
                    response = on_input(user_input)
                    time.sleep(0.5)  # Simulate processing
                
                if response:
                    self.add_message('assistant', response)
                    self._render_message_cli(console, self.messages[-1])
                    
    def _render_message_cli(self, console: Console, message: Dict):
        """Render a single message in CLI."""
        role = message.get('role', 'unknown')
        content = message.get('content', '')
        timestamp = message.get('timestamp', '')
        
        # Style based on role
        if role == 'user':
            style = "bold green"
            icon = "👤"
            title = "You"
        elif role == 'assistant':
            style = "bold blue"
            icon = "🤖"
            title = "Agent"
        else:
            style = "bold yellow"
            icon = "⚙️"
            title = "System"
        
        # Format message
        formatted_content = f"[{style}]{icon} {title}[/{style}] [{timestamp[-8:]}]\n\n{content}"
        
        console.print(Panel(
            formatted_content,
            border_style=style.split()[-1],
            padding=(1, 2)
        ))
        
    def render_streamlit(self, on_submit: Optional[Callable] = None):
        """
        Render chat interface in Streamlit.
        
        Args:
            on_submit: Callback function for message submission
        """
        st.markdown("### 💬 Chat with Agent")
        
        # Chat container
        chat_container = st.container()
        
        with chat_container:
            # Display messages
            for message in self.messages:
                self._render_message_streamlit(message)
        
        # Input area
        st.markdown("---")
        
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_input(
                "Your message",
                placeholder="Type your message here...",
                key="chat_input",
                label_visibility="collapsed"
            )
        
        with col2:
            send_button = st.button("Send", use_container_width=True)
        
        # Handle submission
        if send_button and user_input:
            # Add user message
            self.add_message('user', user_input)
            
            # Process with agent
            if on_submit:
                with st.spinner("Agent is thinking..."):
                    response = on_submit(user_input)
                    time.sleep(0.5)
                
                if response:
                    self.add_message('assistant', response)
            
            # Rerun to update display
            st.rerun()
            
        # Quick actions
        st.markdown("#### Quick Actions")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📋 Summarize", use_container_width=True):
                self.add_message('user', "Please summarize our conversation")
                st.rerun()
        
        with col2:
            if st.button("🔍 Search Memory", use_container_width=True):
                self.add_message('user', "Search my memory")
                st.rerun()
        
        with col3:
            if st.button("📊 Show Stats", use_container_width=True):
                self.add_message('user', "Show usage statistics")
                st.rerun()
        
        with col4:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                self.messages = []
                st.rerun()
                
    def _render_message_streamlit(self, message: Dict):
        """Render a single message in Streamlit."""
        role = message.get('role', 'unknown')
        content = message.get('content', '')
        timestamp = message.get('timestamp', '')
        
        # Determine alignment and color
        if role == 'user':
            align = "flex-end"
            bg_color = "#007bff"
            text_color = "white"
            icon = "👤"
        elif role == 'assistant':
            align = "flex-start"
            bg_color = "#f1f3f4"
            text_color = "#202124"
            icon = "🤖"
        else:
            align = "center"
            bg_color = "#fff3cd"
            text_color = "#856404"
            icon = "⚙️"
        
        # Render message
        st.markdown(f"""
        <div style="
            display: flex;
            justify-content: {align};
            margin: 12px 0;
        ">
            <div style="
                max-width: 70%;
                background-color: {bg_color};
                color: {text_color};
                padding: 12px 16px;
                border-radius: 12px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            ">
                <div style="
                    font-size: 12px;
                    opacity: 0.7;
                    margin-bottom: 4px;
                ">
                    {icon} {role.capitalize()} • {timestamp[-8:]}
                </div>
                <div style="
                    line-height: 1.5;
                    white-space: pre-wrap;
                ">
                    {content}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    def export_conversation(self, format: str = 'json') -> str:
        """
        Export conversation in specified format.
        
        Args:
            format: Export format ('json', 'markdown', 'text')
            
        Returns:
            Exported conversation string
        """
        if format == 'json':
            import json
            return json.dumps(self.messages, indent=2)
        
        elif format == 'markdown':
            lines = ["# Conversation Export\n"]
            for msg in self.messages:
                role = msg.get('role', 'unknown').capitalize()
                content = msg.get('content', '')
                timestamp = msg.get('timestamp', '')
                lines.append(f"## {role} ({timestamp})\n")
                lines.append(f"{content}\n\n")
            return "\n".join(lines)
        
        elif format == 'text':
            lines = []
            for msg in self.messages:
                role = msg.get('role', 'unknown').upper()
                content = msg.get('content', '')
                timestamp = msg.get('timestamp', '')
                lines.append(f"[{timestamp}] {role}: {content}\n")
            return "\n".join(lines)
        
        return ""
        
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the conversation."""
        summary = {
            'total_messages': len(self.messages),
            'user_messages': sum(1 for m in self.messages if m['role'] == 'user'),
            'assistant_messages': sum(1 for m in self.messages if m['role'] == 'assistant'),
            'system_messages': sum(1 for m in self.messages if m['role'] == 'system'),
            'total_characters': sum(len(m['content']) for m in self.messages),
            'start_time': self.messages[0]['timestamp'] if self.messages else None,
            'end_time': self.messages[-1]['timestamp'] if self.messages else None
        }
        return summary
        
    @staticmethod
    def render_conversation_sidebar_streamlit(conversations: List[Dict]):
        """
        Render conversation history sidebar in Streamlit.
        
        Args:
            conversations: List of previous conversations
        """
        with st.sidebar:
            st.markdown("## 💬 Conversations")
            
            for i, conv in enumerate(conversations):
                conv_id = conv.get('id', f'conv-{i}')
                title = conv.get('title', 'Untitled')
                timestamp = conv.get('timestamp', '')
                message_count = conv.get('message_count', 0)
                
                with st.expander(f"{title}", expanded=False):
                    st.caption(f"📅 {timestamp}")
                    st.caption(f"💬 {message_count} messages")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Open", key=f"open-{conv_id}"):
                            st.session_state.current_conversation = conv_id
                    with col2:
                        if st.button("Delete", key=f"delete-{conv_id}"):
                            st.session_state.delete_conversation = conv_id
                            
            st.markdown("---")
            if st.button("➕ New Conversation", use_container_width=True):
                st.session_state.new_conversation = True
                
    @staticmethod
    def render_typing_indicator_cli(console: Console, duration: float = 2.0):
        """
        Show typing indicator in CLI.
        
        Args:
            console: Rich console instance
            duration: Duration to show indicator
        """
        with Live(
            Spinner("dots", text="[bold yellow]Agent is typing...", style="yellow"),
            console=console,
            refresh_per_second=10
        ):
            time.sleep(duration)
            
    @staticmethod
    def render_typing_indicator_streamlit():
        """Show typing indicator in Streamlit."""
        st.markdown("""
        <div style="
            display: flex;
            align-items: center;
            padding: 12px;
            margin: 8px 0;
        ">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
            <span style="margin-left: 12px; color: #666;">Agent is typing...</span>
        </div>
        
        <style>
            .typing-indicator {
                display: flex;
                gap: 4px;
            }
            .typing-indicator span {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background-color: #007bff;
                animation: typing 1.4s infinite;
            }
            .typing-indicator span:nth-child(2) {
                animation-delay: 0.2s;
            }
            .typing-indicator span:nth-child(3) {
                animation-delay: 0.4s;
            }
            @keyframes typing {
                0%, 60%, 100% {
                    transform: translateY(0);
                    opacity: 0.3;
                }
                30% {
                    transform: translateY(-10px);
                    opacity: 1;
                }
            }
        </style>
        """, unsafe_allow_html=True)
        
    def clear_conversation(self):
        """Clear all messages from conversation."""
        self.messages = []
        
    def get_last_n_messages(self, n: int) -> List[Dict]:
        """
        Get last N messages from conversation.
        
        Args:
            n: Number of messages to retrieve
            
        Returns:
            List of last N messages
        """
        return self.messages[-n:] if len(self.messages) >= n else self.messages