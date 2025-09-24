"""
Job Orchestration Framework for MapleHustleCAN
Manages complex workflows and task dependencies
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from celery.result import AsyncResult

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"


class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskNode:
    """Represents a task in a workflow"""
    task_id: str
    task_name: str
    dependencies: List[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 300
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class Workflow:
    """Represents a complete workflow"""
    workflow_id: str
    name: str
    tasks: Dict[str, TaskNode]
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: str = None


class WorkflowOrchestrator:
    """Orchestrates complex workflows with task dependencies"""

    def __init__(self):
        self.active_workflows: Dict[str, Workflow] = {}
        self.task_registry: Dict[str, Callable] = {}

    def register_task(self, task_name: str, task_func: Callable):
        """Register a task function"""
        self.task_registry[task_name] = task_func
        logger.info(f"Registered task: {task_name}")

    def create_workflow(self, workflow_id: str, name: str,
                        tasks: List[Dict[str, Any]]) -> Workflow:
        """Create a new workflow"""
        task_nodes = {}

        for task_config in tasks:
            task_id = task_config['task_id']
            task_node = TaskNode(
                task_id=task_id,
                task_name=task_config['task_name'],
                dependencies=task_config.get('dependencies', []),
                max_retries=task_config.get('max_retries', 3),
                timeout=task_config.get('timeout', 300)
            )
            task_nodes[task_id] = task_node

        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            tasks=task_nodes,
            created_at=datetime.utcnow()
        )

        self.active_workflows[workflow_id] = workflow
        logger.info(f"Created workflow: {workflow_id}")
        return workflow

    async def execute_workflow(self, workflow_id: str) -> Workflow:
        """Execute a workflow with dependency management"""
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow = self.active_workflows[workflow_id]
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.utcnow()

        logger.info(f"Starting workflow: {workflow_id}")

        try:
            # Execute tasks in dependency order
            completed_tasks = set()
            failed_tasks = set()

            while len(completed_tasks) + \
                    len(failed_tasks) < len(workflow.tasks):
                # Find tasks ready to execute
                ready_tasks = self._get_ready_tasks(
                    workflow, completed_tasks, failed_tasks)

                if not ready_tasks:
                    # No ready tasks but not all completed - circular
                    # dependency or error
                    remaining = set(workflow.tasks.keys()) - \
                        completed_tasks - failed_tasks
                    workflow.status = WorkflowStatus.FAILED
                    workflow.error = f"Circular dependency or stuck tasks: {remaining}"
                    return workflow

                # Execute ready tasks concurrently
                tasks_to_execute = []
                for task_id in ready_tasks:
                    task_node = workflow.tasks[task_id]
                    task_node.status = TaskStatus.RUNNING
                    task_node.started_at = datetime.utcnow()

                    # Create Celery task
                    celery_task = self._create_celery_task(task_node)
                    tasks_to_execute.append((task_id, celery_task))

                # Wait for tasks to complete
                for task_id, celery_task in tasks_to_execute:
                    try:
                        result = await self._wait_for_task(celery_task, workflow.tasks[task_id])
                        workflow.tasks[task_id].status = TaskStatus.SUCCESS
                        workflow.tasks[task_id].result = result
                        workflow.tasks[task_id].completed_at = datetime.utcnow()
                        completed_tasks.add(task_id)
                        logger.info(f"Task {task_id} completed successfully")
                    except Exception as e:
                        workflow.tasks[task_id].status = TaskStatus.FAILURE
                        workflow.tasks[task_id].error = str(e)
                        workflow.tasks[task_id].completed_at = datetime.utcnow()
                        failed_tasks.add(task_id)
                        logger.error(f"Task {task_id} failed: {e}")

            # Check if all tasks completed successfully
            if len(failed_tasks) == 0:
                workflow.status = WorkflowStatus.COMPLETED
                workflow.completed_at = datetime.utcnow()
                logger.info(f"Workflow {workflow_id} completed successfully")
            else:
                workflow.status = WorkflowStatus.FAILED
                workflow.error = f"Failed tasks: {failed_tasks}"
                logger.error(f"Workflow {workflow_id} failed")

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.error = str(e)
            workflow.completed_at = datetime.utcnow()
            logger.error(f"Workflow {workflow_id} failed with error: {e}")

        return workflow

    def _get_ready_tasks(
            self,
            workflow: Workflow,
            completed: set,
            failed: set) -> List[str]:
        """Get tasks that are ready to execute (dependencies satisfied)"""
        ready = []

        for task_id, task_node in workflow.tasks.items():
            if task_id in completed or task_id in failed:
                continue

            if task_node.status == TaskStatus.PENDING:
                # Check if all dependencies are completed
                if all(dep in completed for dep in task_node.dependencies):
                    ready.append(task_id)

        return ready

    def _create_celery_task(self, task_node: TaskNode) -> AsyncResult:
        """Create a Celery task for execution"""
        if task_node.task_name not in self.task_registry:
            raise ValueError(f"Task {task_node.task_name} not registered")

        task_func = self.task_registry[task_node.task_name]

        # Apply Celery task decorator
        celery_task = celery_app.task(
            bind=True,
            max_retries=task_node.max_retries,
            time_limit=task_node.timeout
        )(task_func)

        return celery_task.delay()

    async def _wait_for_task(
            self,
            celery_task: AsyncResult,
            task_node: TaskNode) -> Any:
        """Wait for a Celery task to complete"""
        timeout = task_node.timeout

        while not celery_task.ready():
            await asyncio.sleep(1)
            timeout -= 1

            if timeout <= 0:
                celery_task.revoke()
                raise TimeoutError(f"Task {task_node.task_id} timed out")

        if celery_task.successful():
            return celery_task.result
        else:
            raise Exception(f"Task failed: {celery_task.result}")

    def get_workflow_status(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow status"""
        return self.active_workflows.get(workflow_id)

    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        if workflow_id not in self.active_workflows:
            return False

        workflow = self.active_workflows[workflow_id]
        if workflow.status == WorkflowStatus.RUNNING:
            # Cancel all running tasks
            for task_node in workflow.tasks.values():
                if task_node.status == TaskStatus.RUNNING:
                    # In real implementation, would revoke Celery tasks
                    task_node.status = TaskStatus.REVOKED

            workflow.status = WorkflowStatus.CANCELLED
            workflow.completed_at = datetime.utcnow()
            logger.info(f"Workflow {workflow_id} cancelled")
            return True

        return False


# Global orchestrator instance
workflow_orchestrator = WorkflowOrchestrator()


# Example workflow definitions
class WorkflowTemplates:
    """Predefined workflow templates"""

    @staticmethod
    def user_onboarding_workflow(user_id: str) -> Workflow:
        """User onboarding workflow"""
        tasks = [
            {
                'task_id': 'send_welcome_email',
                'task_name': 'send_welcome_email',
                'dependencies': [],
                'timeout': 60
            },
            {
                'task_id': 'create_user_profile',
                'task_name': 'create_user_profile',
                'dependencies': [],
                'timeout': 30
            },
            {
                'task_id': 'setup_notifications',
                'task_name': 'setup_notifications',
                'dependencies': ['create_user_profile'],
                'timeout': 30
            },
            {
                'task_id': 'send_onboarding_guide',
                'task_name': 'send_onboarding_guide',
                'dependencies': ['send_welcome_email', 'setup_notifications'],
                'timeout': 60
            }
        ]

        return workflow_orchestrator.create_workflow(
            workflow_id=f"user_onboarding_{user_id}",
            name="User Onboarding",
            tasks=tasks
        )

    @staticmethod
    def service_creation_workflow(service_id: str) -> Workflow:
        """Service creation workflow"""
        tasks = [
            {
                'task_id': 'validate_service',
                'task_name': 'validate_service',
                'dependencies': [],
                'timeout': 30
            },
            {
                'task_id': 'create_availability',
                'task_name': 'create_availability',
                'dependencies': ['validate_service'],
                'timeout': 60
            },
            {
                'task_id': 'notify_admin',
                'task_name': 'notify_admin',
                'dependencies': ['validate_service'],
                'timeout': 30
            },
            {
                'task_id': 'index_for_search',
                'task_name': 'index_for_search',
                'dependencies': ['create_availability'],
                'timeout': 120
            }
        ]

        return workflow_orchestrator.create_workflow(
            workflow_id=f"service_creation_{service_id}",
            name="Service Creation",
            tasks=tasks
        )

    @staticmethod
    def order_processing_workflow(order_id: str) -> Workflow:
        """Order processing workflow"""
        tasks = [
            {
                'task_id': 'validate_order',
                'task_name': 'validate_order',
                'dependencies': [],
                'timeout': 30
            },
            {
                'task_id': 'process_payment',
                'task_name': 'process_payment',
                'dependencies': ['validate_order'],
                'timeout': 120
            },
            {
                'task_id': 'update_inventory',
                'task_name': 'update_inventory',
                'dependencies': ['process_payment'],
                'timeout': 60
            },
            {
                'task_id': 'send_confirmation',
                'task_name': 'send_confirmation',
                'dependencies': ['process_payment'],
                'timeout': 30
            },
            {
                'task_id': 'schedule_fulfillment',
                'task_name': 'schedule_fulfillment',
                'dependencies': ['update_inventory', 'send_confirmation'],
                'timeout': 30
            }
        ]

        return workflow_orchestrator.create_workflow(
            workflow_id=f"order_processing_{order_id}",
            name="Order Processing",
            tasks=tasks
        )


# Celery tasks for workflow execution
@celery_app.task(bind=True)
def execute_workflow_task(self, workflow_id: str):
    """Execute a workflow as a Celery task"""
    try:
        # This would run in a separate process
        # For now, just log the workflow execution
        logger.info(f"Executing workflow: {workflow_id}")
        return f"Workflow {workflow_id} executed"
    except Exception as e:
        logger.error(f"Workflow {workflow_id} failed: {e}")
        raise


# Export main components
__all__ = [
    'TaskStatus',
    'WorkflowStatus',
    'TaskNode',
    'Workflow',
    'WorkflowOrchestrator',
    'workflow_orchestrator',
    'WorkflowTemplates',
    'execute_workflow_task'
]
