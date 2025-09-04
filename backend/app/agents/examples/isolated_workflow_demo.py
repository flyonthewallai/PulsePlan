"""
Demonstration of Enhanced Workflow Architecture
Shows isolation, error boundaries, state management, and recovery features
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging to see the enhanced features in action
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import the enhanced orchestrator
from ..orchestrator import agent_orchestrator
from ..graphs.base import WorkflowType

logger = logging.getLogger(__name__)


async def demo_basic_workflow_execution():
    """Demonstrate basic workflow execution with isolation"""
    print("\n=== Basic Workflow Execution with Isolation ===")
    
    try:
        result = await agent_orchestrator.execute_workflow(
            workflow_type=WorkflowType.TASK,
            user_id="demo_user_123",
            input_data={
                "operation": "create",
                "task_data": {
                    "title": "Demo Task for Architecture Test",
                    "description": "Testing the new isolated workflow architecture",
                    "priority": "high"
                }
            },
            user_context={
                "email": "demo@example.com",
                "preferences": {"notifications": True}
            },
            resource_limits={
                "max_execution_time": 60.0,  # 1 minute limit
                "max_memory_mb": 128
            }
        )
        
        print(f"✅ Workflow completed successfully!")
        print(f"   Workflow ID: {result.get('workflow_id')}")
        print(f"   Execution Time: {result.get('execution_time', 0):.2f}s")
        print(f"   Nodes Executed: {result.get('nodes_executed', 0)}")
        
        return result["workflow_id"]
        
    except Exception as e:
        print(f"❌ Workflow failed: {str(e)}")
        return None


async def demo_workflow_recovery():
    """Demonstrate workflow recovery mechanisms"""
    print("\n=== Workflow Recovery Demonstration ===")
    
    try:
        # First, try to execute a workflow that might fail
        result = await agent_orchestrator.execute_workflow(
            workflow_type=WorkflowType.SEARCH,
            user_id="demo_user_456",
            input_data={
                "query": "This might timeout or fail"
            },
            resource_limits={
                "max_execution_time": 0.1  # Very short timeout to trigger failure
            }
        )
        
        workflow_id = result["workflow_id"]
        print(f"✅ Workflow unexpectedly succeeded: {workflow_id}")
        
    except Exception as e:
        print(f"⚠️  Workflow failed as expected: {str(e)}")
        
        # Try to find and recover failed workflows
        print("Attempting batch recovery...")
        recovered_ids = await agent_orchestrator.batch_recover_failed_workflows(max_workflows=5)
        
        if recovered_ids:
            print(f"✅ Successfully recovered {len(recovered_ids)} workflows:")
            for wf_id in recovered_ids:
                print(f"   - {wf_id}")
        else:
            print("ℹ️  No workflows were recovered")


async def demo_checkpoint_and_resume():
    """Demonstrate checkpoint creation and workflow suspension/resumption"""
    print("\n=== Checkpoint and Resume Demonstration ===")
    
    try:
        # Execute a long-running workflow
        result = await agent_orchestrator.execute_workflow(
            workflow_type=WorkflowType.BRIEFING,
            user_id="demo_user_789",
            input_data={
                "delivery_method": "api"
            }
        )
        
        workflow_id = result["workflow_id"]
        print(f"✅ Workflow started: {workflow_id}")
        
        # Create a checkpoint
        checkpoint_created = await agent_orchestrator.create_checkpoint(
            workflow_id, 
            "demo_checkpoint"
        )
        
        if checkpoint_created:
            print(f"✅ Checkpoint created for workflow {workflow_id}")
            
            # Demonstrate suspension and resumption
            suspended = await agent_orchestrator.suspend_workflow(
                workflow_id, 
                "Demo suspension for testing"
            )
            
            if suspended:
                print(f"⏸️  Workflow {workflow_id} suspended")
                
                # Wait a moment then resume
                await asyncio.sleep(1)
                
                resumed = await agent_orchestrator.resume_workflow(workflow_id)
                if resumed:
                    print(f"▶️  Workflow {workflow_id} resumed")
                else:
                    print(f"❌ Failed to resume workflow {workflow_id}")
            else:
                print(f"❌ Failed to suspend workflow {workflow_id}")
        else:
            print(f"❌ Failed to create checkpoint for workflow {workflow_id}")
            
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")


async def demo_custom_recovery_handler():
    """Demonstrate custom recovery handler registration"""
    print("\n=== Custom Recovery Handler Demonstration ===")
    
    async def custom_task_recovery_handler(workflow_id: str, state: Dict[str, Any]) -> bool:
        """Custom recovery handler for task workflows"""
        print(f"🔧 Custom recovery handler called for workflow {workflow_id}")
        
        # Simulate custom recovery logic
        error_info = state.get("error", {})
        if "timeout" in str(error_info.get("message", "")).lower():
            print("   Handling timeout error with extended deadline")
            return True
        elif "connection" in str(error_info.get("message", "")).lower():
            print("   Handling connection error with retry")
            return True
        else:
            print("   Cannot recover from this error type")
            return False
    
    # Register the custom handler
    agent_orchestrator.register_recovery_handler("task", custom_task_recovery_handler)
    
    # Set a recovery policy
    agent_orchestrator.set_recovery_policy("task", {
        "default_strategy": "fallback",
        "max_attempts": 5,
        "backoff_multiplier": 1.5
    })
    
    print("✅ Custom recovery handler and policy registered for task workflows")


async def demo_metrics_and_monitoring():
    """Demonstrate metrics and monitoring capabilities"""
    print("\n=== Metrics and Monitoring Demonstration ===")
    
    # Get comprehensive metrics
    metrics = agent_orchestrator.get_workflow_metrics()
    
    print("📊 Current Workflow Metrics:")
    print("   Orchestrator:")
    orchestrator_metrics = metrics.get("orchestrator", {})
    print(f"     - Total Executions: {orchestrator_metrics.get('execution_metrics', {}).get('total_executions', 0)}")
    print(f"     - Isolated Executions: {orchestrator_metrics.get('execution_metrics', {}).get('isolated_executions', 0)}")
    print(f"     - Recovery Attempts: {orchestrator_metrics.get('execution_metrics', {}).get('recovery_attempts', 0)}")
    print(f"     - Success Rate: {orchestrator_metrics.get('success_rate', 0)}%")
    print(f"     - Isolation Enabled: {orchestrator_metrics.get('isolation_enabled', False)}")
    
    # State Manager metrics
    if "state_manager" in metrics:
        state_metrics = metrics["state_manager"]
        print("   State Manager:")
        print(f"     - Active States: {state_metrics.get('active_states', 0)}")
        print(f"     - Total Snapshots: {state_metrics.get('total_snapshots', 0)}")
        print(f"     - Recovery Points: {state_metrics.get('total_recovery_points', 0)}")
    
    # Error Boundary metrics  
    if "error_boundary" in metrics:
        error_metrics = metrics["error_boundary"]
        print("   Error Boundary:")
        print(f"     - Recent Errors: {error_metrics.get('recent_errors', 0)}")
        print(f"     - Circuit Breakers: {len(error_metrics.get('circuit_breakers', {}))}")
    
    # Recovery Service metrics
    if "recovery_service" in metrics:
        recovery_metrics = metrics["recovery_service"]
        print("   Recovery Service:")
        print(f"     - Total Attempts: {recovery_metrics.get('total_attempts', 0)}")
        print(f"     - Success Rate: {recovery_metrics.get('success_rate', 0)}%")
        print(f"     - Active Recoveries: {recovery_metrics.get('active_recoveries', 0)}")


async def main():
    """Main demonstration function"""
    print("🚀 Enhanced Workflow Architecture Demonstration")
    print("=" * 60)
    
    try:
        # Run all demonstrations
        workflow_id = await demo_basic_workflow_execution()
        await demo_workflow_recovery()
        
        if workflow_id:
            await demo_checkpoint_and_resume()
        
        await demo_custom_recovery_handler()
        await demo_metrics_and_monitoring()
        
        print("\n" + "=" * 60)
        print("✅ Demonstration completed successfully!")
        print("🎯 Key features demonstrated:")
        print("   - Isolated workflow execution with resource limits")
        print("   - Automatic error boundary protection")
        print("   - State management with checkpoints")
        print("   - Automated recovery mechanisms")
        print("   - Custom recovery handlers")
        print("   - Comprehensive metrics and monitoring")
        
    except Exception as e:
        print(f"\n❌ Demonstration failed: {str(e)}")
        logger.exception("Demo error")


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(main())