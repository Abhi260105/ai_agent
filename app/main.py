"""
Application Entry Point
Main entry for the AI Agent application
"""
import sys
import argparse
from typing import Optional
from pathlib import Path

from app.config import config
from app.utils.logger import get_logger
from app.schemas.state_schema import AgentState
from app.schemas.plan_schema import PlanExecutionResult

logger = get_logger("app.main")


class Agent:
    """
    Main Agent Class
    Orchestrates the entire agent execution flow
    """
    
    def __init__(self):
        """Initialize the agent"""
        logger.info("Initializing AI Agent")
        
        # Validate configuration
        if not config.validate():
            raise RuntimeError("Invalid configuration - check your .env file")
        
        # Log configuration summary
        if config.dev.debug_mode:
            logger.debug("Configuration loaded", config_summary=config.summary())
        
        logger.info(
            "Agent initialized successfully",
            llm_provider=config.llm.provider,
            memory_enabled=config.storage.enable_vector_memory
        )
    
    def execute(self, goal: str, verbose: bool = None) -> PlanExecutionResult:
        """
        Execute a user goal
        
        Args:
            goal: User's objective (e.g., "Check emails and schedule meetings")
            verbose: Override config verbose setting
            
        Returns:
            PlanExecutionResult with execution summary
            
        Example:
            agent = Agent()
            result = agent.execute("Send email to team")
            print(result.action_summary)
        """
        logger.info("Executing goal", goal=goal)
        
        verbose = verbose if verbose is not None else config.agent.verbose
        
        try:
            # TODO: This will be implemented in Phase 2
            # For now, return a placeholder
            
            logger.warning("Agent execution not yet implemented - Phase 2")
            
            # Placeholder result
            from datetime import datetime
            result = PlanExecutionResult(
                plan_id="placeholder",
                objective=goal,
                status="failed",
                error_summary="Agent execution logic not yet implemented (Phase 2)",
                started_at=datetime.now()
            )
            result.mark_completed()
            
            return result
            
        except Exception as e:
            logger.error("Goal execution failed", error=str(e), goal=goal)
            raise
    
    def interactive_mode(self):
        """
        Start interactive mode
        User can enter goals one at a time
        """
        logger.info("Starting interactive mode")
        
        print("\n" + "="*70)
        print("🤖 AI AGENT - INTERACTIVE MODE")
        print("="*70)
        print(config.summary())
        print("\nType 'quit' or 'exit' to stop")
        print("Type 'help' for available commands")
        print("-"*70 + "\n")
        
        while True:
            try:
                # Get user input
                goal = input("📝 Enter goal: ").strip()
                
                # Handle special commands
                if goal.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                if goal.lower() in ['help', 'h', '?']:
                    self._show_help()
                    continue
                
                if goal.lower() == 'clear':
                    print("\033[2J\033[H")  # Clear screen
                    continue
                
                if not goal:
                    continue
                
                # Execute goal
                print(f"\n🚀 Executing: {goal}\n")
                result = self.execute(goal)
                
                # Display results
                self._display_result(result)
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!")
                break
            except Exception as e:
                logger.error("Interactive mode error", error=str(e))
                print(f"\n❌ Error: {e}\n")
    
    def _show_help(self):
        """Show help message"""
        help_text = """
📚 AVAILABLE COMMANDS:
  
  help, h, ?    - Show this help message
  quit, exit, q - Exit interactive mode
  clear         - Clear screen
  
📝 EXAMPLE GOALS:
  
  - Check my emails and schedule any pending meetings
  - Send email to team about project update
  - Search for recent AI research papers
  - Create a summary of today's meetings
  
💡 TIP: Be specific! The more detail you provide, the better the agent performs.
"""
        print(help_text)
    
    def _display_result(self, result: PlanExecutionResult):
        """Display execution result"""
        print("-"*70)
        print(f"📊 EXECUTION RESULT")
        print("-"*70)
        print(f"Status: {result.status.upper()}")
        print(f"Duration: {result.total_duration_seconds:.2f}s")
        print(f"Completed Steps: {len(result.completed_steps)}")
        print(f"Failed Steps: {len(result.failed_steps)}")
        
        if result.action_summary:
            print(f"\n📝 Actions Taken:")
            for action in result.action_summary:
                print(f"  • {action}")
        
        if result.error_summary:
            print(f"\n❌ Error: {result.error_summary}")
        
        print("-"*70 + "\n")


def main():
    """
    Main entry point for command-line execution
    Handles CLI arguments and starts the agent
    """
    parser = argparse.ArgumentParser(
        description="AI Agent - Autonomous Task Execution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --interactive
  %(prog)s --goal "Check my emails and schedule meetings"
  %(prog)s --goal "Send email to team" --verbose
  %(prog)s --config
        """
    )
    
    # Add arguments
    parser.add_argument(
        "--goal", "-g",
        type=str,
        help="Goal to execute"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Start interactive mode"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--config",
        action="store_true",
        help="Show configuration and exit"
    )
    
    parser.add_argument(
        "--web",
        action="store_true",
        help="Start web UI (Streamlit)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"AI Agent v{config.agent.name}"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    try:
        # Show configuration
        if args.config:
            print(config.summary())
            return 0
        
        # Start web UI
        if args.web:
            if not config.ui.enable_web_ui:
                print("❌ Web UI is disabled in config")
                return 1
            
            print("🌐 Starting web UI...")
            print(f"   URL: http://localhost:{config.ui.web_ui_port}")
            print("   Press Ctrl+C to stop")
            
            # Import here to avoid loading Streamlit if not needed
            from app.ui import web
            web.main()
            return 0
        
        # Initialize agent
        agent = Agent()
        
        # Interactive mode
        if args.interactive:
            agent.interactive_mode()
            return 0
        
        # Execute single goal
        if args.goal:
            result = agent.execute(args.goal, verbose=args.verbose)
            agent._display_result(result)
            
            # Exit code based on result
            return 0 if result.status in ["success", "partial_success"] else 1
        
        # No arguments - show help
        parser.print_help()
        return 0
        
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
        return 0
    except Exception as e:
        logger.critical("Application error", error=str(e), exc_info=True)
        print(f"\n❌ Critical Error: {e}")
        if config.dev.debug_mode:
            import traceback
            traceback.print_exc()
        return 1


def run_tests():
    """
    Entry point for running tests
    Called from pytest
    """
    import pytest
    
    test_dir = Path(__file__).parent.parent / "tests"
    
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        return 1
    
    print("🧪 Running tests...")
    return pytest.main([str(test_dir), "-v"])


def run_cli():
    """
    Entry point for CLI interface
    Called from console_scripts
    """
    from app.ui import cli
    return cli.main()


# Entry point when running as module: python -m app.main
if __name__ == "__main__":
    sys.exit(main())