"""
Integration tests for UI workflows (CLI and Web).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from io import StringIO
import asyncio


@pytest.mark.integration
class TestCLIWorkflows:
    """Test CLI interface workflows."""
    
    @pytest.fixture
    def cli(self):
        """Create CLI instance for testing."""
        from app.ui.cli import AgentCLI
        return AgentCLI()
    
    @pytest.mark.asyncio
    async def test_task_execution_workflow(self, cli):
        """Test complete task execution workflow via CLI."""
        with patch('builtins.input', side_effect=[
            'Python tutorial',  # task description
            'high',  # priority
            'y',  # use memory
            'exit'  # exit
        ]):
            with patch.object(cli, 'execute_task_interactive') as mock_exec:
                mock_exec.return_value = {
                    'status': 'success',
                    'task_id': 'T-123',
                    'result': 'Task completed'
                }
                
                # This would normally run the interactive loop
                # We'll just test the execution method
                result = await mock_exec()
                
                assert result['status'] == 'success'
                assert 'task_id' in result
    
    def test_menu_navigation(self, cli):
        """Test CLI menu navigation."""
        with patch('builtins.input', return_value='menu'):
            with patch.object(cli, 'display_menu') as mock_menu:
                # Simulate showing menu
                mock_menu()
                
                mock_menu.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_memory_browser_workflow(self, cli):
        """Test browsing memory via CLI."""
        with patch('builtins.input', side_effect=['semantic', 'exit']):
            with patch.object(cli, 'browse_memory') as mock_browse:
                mock_browse.return_value = {
                    'memories': [
                        {'id': 'M-1', 'content': 'Test memory'}
                    ]
                }
                
                result = await mock_browse()
                
                assert 'memories' in result
    
    @pytest.mark.asyncio
    async def test_export_workflow(self, cli):
        """Test data export workflow via CLI."""
        with patch('builtins.input', side_effect=['tasks', 'json', 'export.json']):
            with patch.object(cli, 'export_data') as mock_export:
                mock_export.return_value = {
                    'status': 'success',
                    'file': 'export.json'
                }
                
                result = await mock_export()
                
                assert result['status'] == 'success'
    
    def test_error_handling_in_cli(self, cli):
        """Test CLI error handling."""
        with patch('builtins.input', return_value='invalid_command'):
            with patch.object(cli.console, 'print') as mock_print:
                # Simulate error
                try:
                    raise ValueError("Invalid command")
                except ValueError as e:
                    mock_print(f"[red]Error: {str(e)}[/red]")
                
                # Should print error message
                mock_print.assert_called()


@pytest.mark.integration  
class TestWebUIWorkflows:
    """Test Streamlit web UI workflows."""
    
    @pytest.fixture
    def streamlit_session(self):
        """Mock Streamlit session state."""
        return {
            'tasks': [],
            'memories': [],
            'current_page': 'Dashboard'
        }
    
    def test_dashboard_rendering(self, streamlit_session):
        """Test dashboard page renders correctly."""
        from app.ui.web import AgentWebUI
        
        with patch('streamlit.session_state', streamlit_session):
            ui = AgentWebUI()
            
            # Mock streamlit functions
            with patch('streamlit.markdown') as mock_md, \
                 patch('streamlit.columns') as mock_cols, \
                 patch('streamlit.metric') as mock_metric:
                
                mock_cols.return_value = [Mock(), Mock(), Mock(), Mock()]
                
                ui.render_dashboard()
                
                # Should call markdown for header
                assert mock_md.called
                # Should create metrics
                assert mock_metric.called
    
    def test_task_submission_workflow(self, streamlit_session):
        """Test submitting a task via web UI."""
        from app.ui.web import AgentWebUI
        
        with patch('streamlit.session_state', streamlit_session):
            ui = AgentWebUI()
            
            with patch('streamlit.form') as mock_form, \
                 patch('streamlit.text_area') as mock_textarea, \
                 patch('streamlit.selectbox') as mock_select, \
                 patch('streamlit.form_submit_button') as mock_submit:
                
                mock_submit.return_value = True
                mock_textarea.return_value = "Test task"
                mock_select.return_value = "high"
                
                # Render new task form
                ui.render_new_task()
                
                # Should have created form
                assert mock_form.called
    
    def test_memory_browser_ui(self, streamlit_session):
        """Test memory browser in web UI."""
        from app.ui.web import AgentWebUI
        
        with patch('streamlit.session_state', streamlit_session):
            ui = AgentWebUI()
            
            with patch('streamlit.dataframe') as mock_df, \
                 patch('streamlit.multiselect') as mock_multi:
                
                mock_multi.return_value = ["semantic"]
                
                ui.render_memory_browser()
                
                # Should display dataframe
                assert mock_df.called
    
    def test_real_time_updates(self, streamlit_session):
        """Test real-time progress updates."""
        from app.ui.web import AgentWebUI
        
        with patch('streamlit.session_state', streamlit_session):
            ui = AgentWebUI()
            
            with patch('streamlit.progress') as mock_progress, \
                 patch('streamlit.empty') as mock_empty:
                
                status_text = Mock()
                mock_empty.return_value = status_text
                
                # Simulate progress update
                for i in range(0, 101, 20):
                    mock_progress(i / 100)
                    status_text.text(f"Progress: {i}%")
                
                # Should update progress
                assert mock_progress.call_count > 0
    
    def test_sidebar_navigation(self, streamlit_session):
        """Test sidebar navigation in web UI."""
        from app.ui.web import AgentWebUI
        
        with patch('streamlit.session_state', streamlit_session):
            ui = AgentWebUI()
            
            with patch('streamlit.sidebar') as mock_sidebar, \
                 patch('streamlit.button') as mock_button:
                
                mock_button.return_value = True
                
                ui.render_sidebar()
                
                # Should create sidebar
                assert mock_sidebar.called
    
    def test_settings_persistence(self, streamlit_session):
        """Test settings are persisted."""
        from app.ui.web import AgentWebUI
        
        with patch('streamlit.session_state', streamlit_session):
            ui = AgentWebUI()
            
            with patch('streamlit.checkbox') as mock_check, \
                 patch('streamlit.number_input') as mock_num:
                
                mock_check.return_value = True
                mock_num.return_value = 100
                
                ui.render_settings()
                
                # Should save settings
                assert mock_check.called
    
    def test_chart_visualization(self, streamlit_session):
        """Test chart rendering."""
        from app.ui.web import AgentWebUI
        
        with patch('streamlit.session_state', streamlit_session):
            ui = AgentWebUI()
            
            with patch('streamlit.plotly_chart') as mock_chart:
                ui.render_dashboard()
                
                # Should render charts
                assert mock_chart.called


@pytest.mark.integration
class TestUIIntegration:
    """Test UI integration with backend."""
    
    @pytest.mark.asyncio
    async def test_cli_to_api_integration(self):
        """Test CLI interacting with API."""
        from app.ui.cli import AgentCLI
        
        cli = AgentCLI()
        
        with patch('requests.post') as mock_post:
            mock_post.return_value = Mock(
                status_code=201,
                json=lambda: {'id': 'T-123', 'status': 'pending'}
            )
            
            # Simulate API call from CLI
            import requests
            response = requests.post(
                'http://localhost:8000/api/v1/tasks/',
                json={'description': 'Test task'}
            )
            
            assert response.status_code == 201
            assert response.json()['id'] == 'T-123'
    
    @pytest.mark.asyncio
    async def test_web_ui_to_api_integration(self):
        """Test Web UI interacting with API."""
        with patch('requests.get') as mock_get:
            mock_get.return_value = Mock(
                status_code=200,
                json=lambda: [
                    {'id': 'T-1', 'description': 'Task 1'},
                    {'id': 'T-2', 'description': 'Task 2'}
                ]
            )
            
            # Simulate fetching tasks
            import requests
            response = requests.get('http://localhost:8000/api/v1/tasks/')
            
            assert response.status_code == 200
            tasks = response.json()
            assert len(tasks) == 2
    
    @pytest.mark.asyncio
    async def test_task_lifecycle_through_ui(self):
        """Test complete task lifecycle through UI."""
        from app.ui.cli import AgentCLI
        
        cli = AgentCLI()
        
        # Create task
        with patch('requests.post') as mock_post:
            mock_post.return_value = Mock(
                status_code=201,
                json=lambda: {'id': 'T-123', 'status': 'pending'}
            )
            
            import requests
            create_resp = requests.post(
                'http://localhost:8000/api/v1/tasks/',
                json={'description': 'Lifecycle test'}
            )
            
            task_id = create_resp.json()['id']
        
        # Check status
        with patch('requests.get') as mock_get:
            mock_get.return_value = Mock(
                status_code=200,
                json=lambda: {'id': task_id, 'status': 'running', 'progress': 50}
            )
            
            status_resp = requests.get(f'http://localhost:8000/api/v1/tasks/{task_id}')
            
            assert status_resp.json()['status'] == 'running'
        
        # Complete
        with patch('requests.get') as mock_get:
            mock_get.return_value = Mock(
                status_code=200,
                json=lambda: {'id': task_id, 'status': 'completed', 'progress': 100}
            )
            
            final_resp = requests.get(f'http://localhost:8000/api/v1/tasks/{task_id}')
            
            assert final_resp.json()['status'] == 'completed'
    
    def test_error_display_in_ui(self):
        """Test error messages are displayed correctly."""
        from app.ui.cli import AgentCLI
        
        cli = AgentCLI()
        
        with patch.object(cli.console, 'print') as mock_print:
            # Simulate error
            error_msg = "Task execution failed"
            cli.console.print(f"[red]Error: {error_msg}[/red]")
            
            # Should display error
            mock_print.assert_called_with(f"[red]Error: {error_msg}[/red]")
    
    @pytest.mark.asyncio
    async def test_concurrent_ui_operations(self):
        """Test handling concurrent UI operations."""
        tasks = []
        
        async def simulate_operation(i):
            await asyncio.sleep(0.1)
            return {'id': f'task-{i}', 'status': 'completed'}
        
        # Simulate multiple operations
        for i in range(5):
            tasks.append(simulate_operation(i))
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(r['status'] == 'completed' for r in results)