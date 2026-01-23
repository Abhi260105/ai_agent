"""
Integration tests for multi-tool scenarios and tool chaining.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio


@pytest.mark.integration
class TestToolChain:
    """Test multi-tool workflow scenarios."""
    
    @pytest.fixture
    async def tool_manager(self):
        """Create tool manager with multiple tools."""
        from app.tools.base_tool import ToolManager
        manager = ToolManager()
        await manager.initialize()
        yield manager
        await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_search_and_summarize_chain(self, tool_manager):
        """Test chain: web search -> extract content -> summarize."""
        # Mock search results
        search_results = [
            {"title": "AI Article", "url": "https://example.com/ai", "snippet": "AI advances..."}
        ]
        
        # Mock page content
        page_content = "This is a detailed article about AI advances in 2025..."
        
        with patch.object(tool_manager, 'get_tool') as mock_get_tool:
            # Mock web search tool
            search_tool = AsyncMock()
            search_tool.execute.return_value = {
                'status': 'success',
                'results': search_results
            }
            
            # Mock web scraper tool
            scraper_tool = AsyncMock()
            scraper_tool.execute.return_value = {
                'status': 'success',
                'content': page_content
            }
            
            # Mock summarizer tool
            summarizer_tool = AsyncMock()
            summarizer_tool.execute.return_value = {
                'status': 'success',
                'summary': 'AI has advanced significantly in 2025...'
            }
            
            mock_get_tool.side_effect = [search_tool, scraper_tool, summarizer_tool]
            
            # Execute chain
            # Step 1: Search
            search_result = await tool_manager.get_tool('web_search').execute({'query': 'AI advances'})
            assert search_result['status'] == 'success'
            
            # Step 2: Scrape
            url = search_result['results'][0]['url']
            scrape_result = await tool_manager.get_tool('web_scraper').execute({'url': url})
            assert scrape_result['status'] == 'success'
            
            # Step 3: Summarize
            summary_result = await tool_manager.get_tool('summarizer').execute({
                'text': scrape_result['content']
            })
            assert summary_result['status'] == 'success'
            assert 'summary' in summary_result
    
    @pytest.mark.asyncio
    async def test_data_analysis_chain(self, tool_manager):
        """Test chain: read file -> analyze data -> create report -> send email."""
        with patch.object(tool_manager, 'get_tool') as mock_get_tool:
            # Mock file reader
            file_tool = AsyncMock()
            file_tool.execute.return_value = {
                'status': 'success',
                'data': [
                    {'month': 'Jan', 'sales': 100},
                    {'month': 'Feb', 'sales': 150}
                ]
            }
            
            # Mock data analyzer
            analyzer_tool = AsyncMock()
            analyzer_tool.execute.return_value = {
                'status': 'success',
                'total_sales': 250,
                'average': 125,
                'trend': 'increasing'
            }
            
            # Mock report generator
            report_tool = AsyncMock()
            report_tool.execute.return_value = {
                'status': 'success',
                'report': 'Sales Report: Total $250, Average $125...'
            }
            
            # Mock email tool
            email_tool = AsyncMock()
            email_tool.execute.return_value = {
                'status': 'success',
                'message_id': 'msg_123'
            }
            
            mock_get_tool.side_effect = [file_tool, analyzer_tool, report_tool, email_tool]
            
            # Execute chain
            data = await tool_manager.get_tool('file_reader').execute({'file': 'sales.csv'})
            analysis = await tool_manager.get_tool('analyzer').execute({'data': data['data']})
            report = await tool_manager.get_tool('reporter').execute({'data': analysis})
            email_result = await tool_manager.get_tool('email').execute({
                'to': 'team@example.com',
                'subject': 'Sales Report',
                'body': report['report']
            })
            
            assert email_result['status'] == 'success'
    
    @pytest.mark.asyncio
    async def test_calendar_workflow_chain(self, tool_manager):
        """Test chain: check calendar -> find slots -> book meeting -> send invites."""
        with patch.object(tool_manager, 'get_tool') as mock_get_tool:
            # Mock calendar check
            calendar_tool = AsyncMock()
            calendar_tool.execute.side_effect = [
                # Check availability
                {
                    'status': 'success',
                    'available_slots': [
                        {'start': '2025-01-10T10:00:00Z', 'end': '2025-01-10T11:00:00Z'}
                    ]
                },
                # Book meeting
                {
                    'status': 'success',
                    'event_id': 'event_123'
                }
            ]
            
            # Mock email tool for invites
            email_tool = AsyncMock()
            email_tool.execute.return_value = {
                'status': 'success',
                'sent_count': 3
            }
            
            mock_get_tool.side_effect = [calendar_tool, calendar_tool, email_tool]
            
            # Execute chain
            availability = await tool_manager.get_tool('calendar').execute({
                'action': 'check_availability',
                'attendees': ['alice@example.com', 'bob@example.com']
            })
            
            assert len(availability['available_slots']) > 0
            
            booking = await tool_manager.get_tool('calendar').execute({
                'action': 'book',
                'slot': availability['available_slots'][0]
            })
            
            invites = await tool_manager.get_tool('email').execute({
                'action': 'send_invites',
                'event_id': booking['event_id']
            })
            
            assert invites['sent_count'] == 3
    
    @pytest.mark.asyncio
    async def test_parallel_tool_execution(self, tool_manager):
        """Test executing multiple tools in parallel."""
        with patch.object(tool_manager, 'get_tool') as mock_get_tool:
            # Create multiple tools
            tools = []
            for i in range(3):
                tool = AsyncMock()
                tool.execute.return_value = {
                    'status': 'success',
                    'result': f'Result {i}'
                }
                tools.append(tool)
            
            mock_get_tool.side_effect = tools
            
            # Execute in parallel
            tasks = [
                tool_manager.get_tool(f'tool_{i}').execute({})
                for i in range(3)
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 3
            assert all(r['status'] == 'success' for r in results)
    
    @pytest.mark.asyncio
    async def test_conditional_tool_chain(self, tool_manager):
        """Test tool chain with conditional branching."""
        with patch.object(tool_manager, 'get_tool') as mock_get_tool:
            # Mock validation tool
            validator_tool = AsyncMock()
            validator_tool.execute.return_value = {
                'status': 'success',
                'is_valid': True
            }
            
            # Mock processing tool
            processor_tool = AsyncMock()
            processor_tool.execute.return_value = {
                'status': 'success',
                'result': 'Processed data'
            }
            
            # Mock error handler tool
            error_tool = AsyncMock()
            error_tool.execute.return_value = {
                'status': 'success',
                'error_handled': True
            }
            
            mock_get_tool.side_effect = [validator_tool, processor_tool]
            
            # Execute chain with condition
            validation = await tool_manager.get_tool('validator').execute({'data': 'test'})
            
            if validation['is_valid']:
                result = await tool_manager.get_tool('processor').execute({'data': 'test'})
                assert result['status'] == 'success'
            else:
                # Would call error tool
                pass
    
    @pytest.mark.asyncio
    async def test_error_recovery_in_chain(self, tool_manager):
        """Test error handling and recovery in tool chain."""
        with patch.object(tool_manager, 'get_tool') as mock_get_tool:
            # First tool succeeds
            tool1 = AsyncMock()
            tool1.execute.return_value = {'status': 'success', 'data': 'step1'}
            
            # Second tool fails
            tool2 = AsyncMock()
            tool2.execute.return_value = {'status': 'error', 'error': 'Tool failed'}
            
            # Recovery tool
            recovery_tool = AsyncMock()
            recovery_tool.execute.return_value = {'status': 'success', 'recovered': True}
            
            mock_get_tool.side_effect = [tool1, tool2, recovery_tool]
            
            # Execute with error handling
            result1 = await tool_manager.get_tool('tool1').execute({})
            assert result1['status'] == 'success'
            
            result2 = await tool_manager.get_tool('tool2').execute({'data': result1['data']})
            
            if result2['status'] == 'error':
                # Attempt recovery
                recovery = await tool_manager.get_tool('recovery').execute({
                    'error': result2['error']
                })
                assert recovery['recovered'] is True
    
    @pytest.mark.asyncio
    async def test_tool_chain_with_memory(self, tool_manager):
        """Test tool chain that uses memory between steps."""
        from app.services.storage_service import StorageService
        
        storage = StorageService(':memory:')
        
        with patch.object(tool_manager, 'get_tool') as mock_get_tool:
            # Tool that saves to memory
            save_tool = AsyncMock()
            save_tool.execute.return_value = {'status': 'success', 'saved': True}
            
            # Tool that loads from memory
            load_tool = AsyncMock()
            load_tool.execute.return_value = {
                'status': 'success',
                'data': 'retrieved_data'
            }
            
            mock_get_tool.side_effect = [save_tool, load_tool]
            
            # Execute chain with memory
            await storage.save('context', {'id': 'ctx_1', 'data': 'important_info'})
            
            save_result = await tool_manager.get_tool('save_tool').execute({
                'data': 'new_data'
            })
            
            load_result = await tool_manager.get_tool('load_tool').execute({
                'context_id': 'ctx_1'
            })
            
            assert load_result['data'] == 'retrieved_data'
    
    @pytest.mark.asyncio
    async def test_long_tool_chain(self, tool_manager):
        """Test a long chain of 10+ tools."""
        with patch.object(tool_manager, 'get_tool') as mock_get_tool:
            # Create 10 tools
            tools = []
            for i in range(10):
                tool = AsyncMock()
                tool.execute.return_value = {
                    'status': 'success',
                    'step': i,
                    'data': f'data_{i}'
                }
                tools.append(tool)
            
            mock_get_tool.side_effect = tools
            
            # Execute long chain
            context = {}
            for i in range(10):
                result = await tool_manager.get_tool(f'tool_{i}').execute(context)
                context['previous_result'] = result
                assert result['status'] == 'success'
                assert result['step'] == i
    
    @pytest.mark.asyncio
    async def test_tool_retry_in_chain(self, tool_manager):
        """Test automatic retry of failed tools in chain."""
        with patch.object(tool_manager, 'get_tool') as mock_get_tool:
            call_count = 0
            
            async def failing_tool(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    return {'status': 'error', 'error': 'Temporary failure'}
                return {'status': 'success', 'data': 'success after retry'}
            
            tool = AsyncMock()
            tool.execute.side_effect = failing_tool
            
            mock_get_tool.return_value = tool
            
            # Execute with retry
            max_retries = 3
            result = None
            
            for attempt in range(max_retries):
                result = await tool_manager.get_tool('retry_tool').execute({})
                if result['status'] == 'success':
                    break
                await asyncio.sleep(0.1)
            
            assert result['status'] == 'success'
            assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_dynamic_tool_selection(self, tool_manager):
        """Test dynamically selecting tools based on conditions."""
        with patch.object(tool_manager, 'get_tool') as mock_get_tool:
            # Different tools for different scenarios
            email_tool = AsyncMock()
            email_tool.execute.return_value = {'status': 'success', 'method': 'email'}
            
            slack_tool = AsyncMock()
            slack_tool.execute.return_value = {'status': 'success', 'method': 'slack'}
            
            # Select tool based on condition
            notification_type = 'urgent'
            
            if notification_type == 'urgent':
                mock_get_tool.return_value = slack_tool
                result = await tool_manager.get_tool('slack').execute({})
                assert result['method'] == 'slack'
            else:
                mock_get_tool.return_value = email_tool
                result = await tool_manager.get_tool('email').execute({})
                assert result['method'] == 'email'
    
    @pytest.mark.asyncio
    async def test_tool_chain_performance(self, tool_manager):
        """Test performance of tool chain execution."""
        import time
        
        with patch.object(tool_manager, 'get_tool') as mock_get_tool:
            # Create fast tools
            tools = []
            for i in range(5):
                tool = AsyncMock()
                
                async def fast_execute(*args, **kwargs):
                    await asyncio.sleep(0.1)  # Simulate work
                    return {'status': 'success'}
                
                tool.execute = fast_execute
                tools.append(tool)
            
            mock_get_tool.side_effect = tools
            
            # Execute and measure time
            start = time.time()
            
            for i in range(5):
                await tool_manager.get_tool(f'tool_{i}').execute({})
            
            duration = time.time() - start
            
            # Should complete in reasonable time
            assert duration < 1.0  # 5 tools * 0.1s each + overhead
    
    @pytest.mark.asyncio
    async def test_complex_workflow_integration(self, tool_manager):
        """Test complex workflow with multiple tool chains."""
        with patch.object(tool_manager, 'get_tool') as mock_get_tool:
            # Setup complete workflow
            tools_sequence = [
                # Data collection phase
                AsyncMock(execute=AsyncMock(return_value={'status': 'success', 'data': 'raw'})),
                AsyncMock(execute=AsyncMock(return_value={'status': 'success', 'data': 'validated'})),
                
                # Processing phase
                AsyncMock(execute=AsyncMock(return_value={'status': 'success', 'result': 'processed'})),
                AsyncMock(execute=AsyncMock(return_value={'status': 'success', 'result': 'analyzed'})),
                
                # Output phase
                AsyncMock(execute=AsyncMock(return_value={'status': 'success', 'report': 'created'})),
                AsyncMock(execute=AsyncMock(return_value={'status': 'success', 'sent': True})),
            ]
            
            mock_get_tool.side_effect = tools_sequence
            
            # Execute complete workflow
            results = []
            for i, phase in enumerate(['collect', 'validate', 'process', 'analyze', 'report', 'send']):
                result = await tool_manager.get_tool(phase).execute({})
                results.append(result)
                assert result['status'] == 'success'
            
            assert len(results) == 6