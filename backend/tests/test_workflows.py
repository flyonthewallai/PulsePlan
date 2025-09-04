"""
Test LangGraph workflows
"""
import pytest
from datetime import datetime

from app.workflows.base import WorkflowType, create_initial_state
from app.workflows.natural_language_workflow import NaturalLanguageWorkflow
from app.workflows.calendar_workflow import CalendarWorkflow
from app.workflows.task_workflow import TaskWorkflow
from app.workflows.briefing_workflow import BriefingWorkflow
from app.workflows.workflow_manager import WorkflowManager


class TestWorkflowBase:
    """Test base workflow functionality"""
    
    def test_create_initial_state(self):
        """Test creating initial workflow state"""
        state = create_initial_state(
            user_id="test_user",
            workflow_type=WorkflowType.NATURAL_LANGUAGE,
            input_data={"query": "schedule a meeting"}
        )
        
        assert state["user_id"] == "test_user"
        assert state["workflow_type"] == "natural_language"
        assert state["input_data"]["query"] == "schedule a meeting"
        assert isinstance(state["execution_start"], datetime)
        assert state["retry_count"] == 0


class TestNaturalLanguageWorkflow:
    """Test natural language processing workflow"""
    
    @pytest.mark.asyncio
    async def test_intent_classification(self):
        """Test intent classification for different queries"""
        workflow = NaturalLanguageWorkflow()
        
        # Test basic classification functionality
        # Note: Actual LLM results may vary, so we test the structure
        state = create_initial_state(
            user_id="test_user",
            workflow_type=WorkflowType.NATURAL_LANGUAGE,
            input_data={"query": "schedule a meeting tomorrow"}
        )
        
        # Mock the LLM to avoid API calls in tests
        original_classify = workflow._classify_intent
        workflow._classify_intent = lambda query: {
            "intent": "calendar",
            "confidence": 0.9,
            "reasoning": "User wants to schedule something",
            "ambiguous": False,
            "alternative_intents": [],
            "raw_response": "Mock response"
        }
        
        try:
            result_state = workflow.intent_classifier_node(state)
            assert "classified_intent" in result_state["input_data"]
            assert "confidence" in result_state["input_data"]
            assert "classification_details" in result_state["input_data"]
            assert result_state["input_data"]["classified_intent"] == "calendar"
            assert result_state["input_data"]["confidence"] == 0.9
        finally:
            workflow._classify_intent = original_classify
    
    @pytest.mark.asyncio
    async def test_ambiguous_intent_handling(self):
        """Test handling of ambiguous intents with clarification"""
        workflow = NaturalLanguageWorkflow()
        
        state = create_initial_state(
            user_id="test_user",
            workflow_type=WorkflowType.NATURAL_LANGUAGE,
            input_data={"query": "make sure I don't forget the group project"}
        )
        
        # Mock ambiguous classification
        original_classify = workflow._classify_intent
        workflow._classify_intent = lambda query: {
            "intent": "task",
            "confidence": 0.5,  # Low confidence triggers ambiguous handling
            "reasoning": "Could be task creation or calendar scheduling",
            "ambiguous": True,
            "alternative_intents": ["calendar"],
            "raw_response": "Mock ambiguous response"
        }
        
        try:
            result_state = workflow.intent_classifier_node(state)
            assert result_state["input_data"]["classified_intent"] == "ambiguous"
            assert result_state["input_data"]["needs_clarification"] == True
            assert "clarification_context" in result_state["input_data"]
            
            # Mock LLM clarification to avoid API calls
            original_llm_clarification = workflow._generate_llm_clarification
            workflow._generate_llm_clarification = lambda query, type, context=None: {
                "workflow_type": "clarification",
                "clarification_type": "ambiguous",
                "original_query": query,
                "message": "Mock clarification message",
                "options": [{"action": "calendar", "description": "Mock option"}],
                "llm_reasoning": "Mock reasoning"
            }
            
            try:
                # Test clarification generation
                clarification_state = workflow.clarification_generator_node(result_state)
                output = clarification_state["output_data"]
                assert output["clarification_type"] == "ambiguous"
                assert "options" in output
                assert len(output["options"]) > 0
            finally:
                workflow._generate_llm_clarification = original_llm_clarification
            
        finally:
            workflow._classify_intent = original_classify
    
    @pytest.mark.asyncio
    async def test_llm_chat_workflow(self):
        """Test LLM-powered chat responses"""
        workflow = NaturalLanguageWorkflow()
        
        state = create_initial_state(
            user_id="test_user",
            workflow_type=WorkflowType.NATURAL_LANGUAGE,
            input_data={"query": "How do I schedule a meeting?", "classified_intent": "chat"}
        )
        
        # Mock LLM chat response
        original_chat_response = workflow._generate_llm_chat_response
        workflow._generate_llm_chat_response = lambda query, context: {
            "response": "Mock helpful response about scheduling",
            "conversation_type": "help",
            "reasoning": "User asking about features",
            "helpful_actions": [{"action": "calendar", "description": "Schedule a meeting", "example_query": "Schedule meeting tomorrow"}],
            "follow_up_questions": ["What time works best?"]
        }
        
        try:
            result_state = workflow.chat_router_node(state)
            output = result_state["output_data"]
            assert output["workflow_type"] == "chat"
            assert "response" in output
            assert "helpful_actions" in output
            assert "follow_up_questions" in output
            assert output["conversation_type"] == "help"
        finally:
            workflow._generate_llm_chat_response = original_chat_response
    
    @pytest.mark.asyncio
    async def test_workflow_execution(self):
        """Test full natural language workflow execution"""
        workflow = NaturalLanguageWorkflow()
        
        state = create_initial_state(
            user_id="test_user",
            workflow_type=WorkflowType.NATURAL_LANGUAGE,
            input_data={"query": "schedule a meeting tomorrow"},
            user_context={"permissions": {"can_execute_workflows": True}}
        )
        
        result = await workflow.execute(state)
        
        assert result["workflow_type"] == "natural_language"
        assert "output_data" in result
        assert result["input_data"]["classified_intent"] == "calendar"
        assert "trace_updater" in result["visited_nodes"]


class TestCalendarWorkflow:
    """Test calendar integration workflow"""
    
    @pytest.mark.asyncio
    async def test_provider_validation(self):
        """Test calendar provider validation"""
        workflow = CalendarWorkflow()
        
        # Test valid provider
        state = create_initial_state(
            user_id="test_user",
            workflow_type=WorkflowType.CALENDAR,
            input_data={"provider": "google", "operation": "list"},
            connected_accounts={"google": {"expires_at": "2024-12-31T23:59:59Z"}}
        )
        
        # Should pass validation
        result_state = workflow.provider_selector_node(state)
        assert result_state["input_data"]["selected_provider"] == "google"
    
    @pytest.mark.asyncio
    async def test_calendar_operations(self):
        """Test different calendar operations"""
        workflow = CalendarWorkflow()
        
        operations = ["list", "create", "update", "delete"]
        
        for operation in operations:
            state = create_initial_state(
                user_id="test_user",
                workflow_type=WorkflowType.CALENDAR,
                input_data={"provider": "google", "operation": operation},
                connected_accounts={"google": {"expires_at": "2024-12-31T23:59:59Z"}}
            )
            
            result = await workflow.execute(state)
            assert result["output_data"]["provider"] == "google"
            assert result["output_data"]["operation"] == operation


class TestTaskWorkflow:
    """Test task management workflow"""
    
    @pytest.mark.asyncio
    async def test_task_type_detection(self):
        """Test task operation type detection"""
        workflow = TaskWorkflow()
        
        test_cases = [
            ({"task_data": {"title": "New task"}}, "create"),
            ({"task_id": "123", "task_data": {"title": "Updated"}}, "update"),
            ({"task_id": "123", "delete": True}, "delete"),
            ({"task_id": "123"}, "get"),
            ({}, "list")
        ]
        
        for input_data, expected_operation in test_cases:
            state = create_initial_state(
                user_id="test_user",
                workflow_type=WorkflowType.TASK,
                input_data=input_data
            )
            
            result_state = workflow.task_type_detector_node(state)
            assert result_state["input_data"]["detected_operation"] == expected_operation
    
    @pytest.mark.asyncio
    async def test_task_creation(self):
        """Test task creation workflow"""
        workflow = TaskWorkflow()
        
        state = create_initial_state(
            user_id="test_user",
            workflow_type=WorkflowType.TASK,
            input_data={
                "operation": "create",
                "task_data": {
                    "title": "Test Task",
                    "description": "Test description",
                    "priority": "high"
                }
            }
        )
        
        result = await workflow.execute(state)
        
        assert result["output_data"]["operation"] == "create"
        assert result["output_data"]["result"]["title"] == "Test Task"
        assert result["output_data"]["result"]["priority"] == "high"


class TestBriefingWorkflow:
    """Test daily briefing workflow"""
    
    @pytest.mark.asyncio
    async def test_data_aggregation(self):
        """Test briefing data aggregation"""
        workflow = BriefingWorkflow()
        
        state = create_initial_state(
            user_id="test_user",
            workflow_type=WorkflowType.BRIEFING,
            input_data={"date": "2024-01-15"},
            connected_accounts={
                "gmail": {"expires_at": "2024-12-31T23:59:59Z"},
                "google": {"expires_at": "2024-12-31T23:59:59Z"}
            }
        )
        
        result_state = workflow.data_aggregator_node(state)
        
        aggregated = result_state["input_data"]["aggregated_data"]
        assert aggregated["briefing_date"] == "2024-01-15"
        assert "gmail" in aggregated["data_sources"]["email"]["accounts"]
        assert "google" in aggregated["data_sources"]["calendar"]["providers"]
    
    @pytest.mark.asyncio
    async def test_briefing_generation(self):
        """Test full briefing generation"""
        workflow = BriefingWorkflow()
        
        state = create_initial_state(
            user_id="test_user",
            workflow_type=WorkflowType.BRIEFING,
            input_data={"delivery_method": "api"},
            connected_accounts={
                "gmail": {"expires_at": "2024-12-31T23:59:59Z"},
                "google": {"expires_at": "2024-12-31T23:59:59Z"}
            }
        )
        
        result = await workflow.execute(state)
        
        assert "briefing" in result["output_data"]
        assert "formatted_text" in result["output_data"]["briefing"]
        assert "content_sections" in result["output_data"]["briefing"]


class TestWorkflowManager:
    """Test workflow manager"""
    
    @pytest.mark.asyncio
    async def test_natural_language_execution(self):
        """Test executing natural language query through manager"""
        manager = WorkflowManager()
        
        result = await manager.execute_natural_language_query(
            user_id="test_user",
            query="create a task for testing",
            user_context={"permissions": {"can_execute_workflows": True}}
        )
        
        assert result["workflow_type"] == "natural_language"
        assert result["status"] == "completed"
        assert "workflow_id" in result
        assert "execution_time" in result
    
    @pytest.mark.asyncio
    async def test_workflow_tracking(self):
        """Test workflow execution tracking"""
        manager = WorkflowManager()
        
        # Execute a workflow
        result = await manager.execute_natural_language_query(
            user_id="test_user", 
            query="test query",
            user_context={"permissions": {"can_execute_workflows": True}}
        )
        
        workflow_id = result["workflow_id"]
        
        # Check that it was tracked
        status = manager.get_workflow_status(workflow_id)
        assert status is not None
        assert status["status"] == "completed"
        assert status["user_id"] == "test_user"
    
    def test_workflow_metrics(self):
        """Test workflow metrics collection"""
        manager = WorkflowManager()
        
        metrics = manager.get_workflow_metrics()
        
        assert "total_workflows" in metrics
        assert "success_rate" in metrics
        assert "workflow_types" in metrics
        assert isinstance(metrics["success_rate"], (int, float))