"""
Extended Thinking module for Lyra
Enables deep contemplation and computation during idle periods
"""

import os
import time
import json
import logging
import threading
import random
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger("extended_thinking")

class ThinkingTask:
    """Represents a single extended thinking task"""
    
    def __init__(self, task_id: str, task_type: str, description: str, 
                priority: float = 0.5, max_duration: int = 300):
        self.task_id = task_id
        self.task_type = task_type  # e.g., "reflection", "concept_refinement", "goal_planning"
        self.description = description
        self.priority = priority  # 0.0 to 1.0, higher = more important
        self.status = "pending"  # "pending", "in_progress", "completed", "interrupted", "failed"
        self.progress = 0.0  # 0.0 to 1.0, how complete the task is
        self.max_duration = max_duration  # maximum duration in seconds
        self.time_spent = 0.0  # time spent on this task so far in seconds
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None
        self.result = None  # result of the thinking task
        self.notes = []  # notes or intermediate thoughts during the process
        self.last_updated = time.time()
        self.tags = []  # List of tags to categorize the task
        self.interruptible = True  # Whether this task can be interrupted
        
    def start(self):
        """Start the thinking task"""
        self.status = "in_progress"
        self.started_at = time.time()
        self.last_updated = time.time()
        
    def update_progress(self, new_progress: float, time_increment: float, note: str = None):
        """Update progress and time spent on the task"""
        self.progress = max(0.0, min(1.0, new_progress))
        self.time_spent += time_increment
        self.last_updated = time.time()
        
        if note:
            self.add_note(note)
            
        # Check if task is now complete
        if self.progress >= 1.0 and self.status != "completed":
            self.complete()
            
    def add_note(self, note: str):
        """Add a note or intermediate thought to the task"""
        self.notes.append({
            "timestamp": time.time(),
            "content": note
        })
        self.last_updated = time.time()
        
    def complete(self, result: Any = None):
        """Mark the task as completed"""
        self.status = "completed"
        self.progress = 1.0
        self.completed_at = time.time()
        if result:
            self.result = result
        self.last_updated = time.time()
        
    def interrupt(self):
        """Interrupt the thinking task"""
        if self.interruptible and self.status == "in_progress":
            self.status = "interrupted"
            self.last_updated = time.time()
            return True
        return False
        
    def resume(self):
        """Resume an interrupted task"""
        if self.status == "interrupted":
            self.status = "in_progress"
            self.last_updated = time.time()
            return True
        return False
        
    def set_result(self, result: Any):
        """Set the result of the thinking task"""
        self.result = result
        self.last_updated = time.time()
        
    def should_timeout(self) -> bool:
        """Check if the task should timeout based on max duration"""
        if self.status != "in_progress" or self.max_duration <= 0:
            return False
            
        return self.time_spent >= self.max_duration
        
    def add_tag(self, tag: str):
        """Add a tag to categorize the task"""
        if tag not in self.tags:
            self.tags.append(tag)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "progress": self.progress,
            "max_duration": self.max_duration,
            "time_spent": self.time_spent,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "notes": self.notes,
            "last_updated": self.last_updated,
            "tags": self.tags,
            "interruptible": self.interruptible
        }
        
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ThinkingTask':
        """Create a task from dictionary data"""
        task = ThinkingTask(
            task_id=data["task_id"],
            task_type=data["task_type"],
            description=data["description"],
            priority=data["priority"],
            max_duration=data["max_duration"]
        )
        task.status = data["status"]
        task.progress = data["progress"]
        task.time_spent = data["time_spent"]
        task.created_at = data["created_at"]
        task.started_at = data["started_at"]
        task.completed_at = data["completed_at"]
        task.result = data["result"]
        task.notes = data["notes"]
        task.last_updated = data["last_updated"]
        task.tags = data.get("tags", [])
        task.interruptible = data.get("interruptible", True)
        return task

class ThinkingTaskManager:
    """Manages extended thinking tasks"""
    
    def __init__(self, save_path: str = None):
        self.pending_tasks = {}  # task_id -> ThinkingTask
        self.active_task = None  # Currently active thinking task
        self.completed_tasks = {}  # task_id -> ThinkingTask
        self.failed_tasks = {}  # task_id -> ThinkingTask
        self.save_path = save_path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                                  "data", "thinking_tasks.json")
        
        # Status flags
        self.is_thinking = False
        self.user_present = True  # Assume user is present initially
        self.last_interaction_time = time.time()
        self.idle_threshold = 300  # 5 minutes of no interaction
        
        # Thinking thread
        self.thinking_thread = None
        self.stop_thinking = threading.Event()
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        
        # Load existing tasks if available
        self.load_tasks()
    
    def create_task(self, task_type: str, description: str, 
                   priority: float = 0.5, max_duration: int = 300) -> ThinkingTask:
        """Create a new thinking task"""
        task_id = f"think_{int(time.time())}_{hash(description) % 10000}"
        
        task = ThinkingTask(
            task_id=task_id,
            task_type=task_type,
            description=description,
            priority=priority,
            max_duration=max_duration
        )
        
        self.pending_tasks[task_id] = task
        
        # Save tasks after adding
        self.save_tasks()
        
        return task
    
    def get_task(self, task_id: str) -> Optional[ThinkingTask]:
        """Get a task by ID"""
        if task_id in self.pending_tasks:
            return self.pending_tasks[task_id]
        elif task_id in self.completed_tasks:
            return self.completed_tasks[task_id]
        elif task_id in self.failed_tasks:
            return self.failed_tasks[task_id]
        elif self.active_task and self.active_task.task_id == task_id:
            return self.active_task
        return None
    
    def start_task(self, task_id: str) -> bool:
        """Start a pending thinking task"""
        if task_id not in self.pending_tasks:
            return False
            
        # Check if another task is active
        if self.active_task:
            # If current task can be interrupted, interrupt it
            if self.active_task.interruptible:
                self.active_task.interrupt()
                self.pending_tasks[self.active_task.task_id] = self.active_task
            else:
                # Cannot interrupt current task
                return False
        
        # Start the selected task
        task = self.pending_tasks.pop(task_id)
        task.start()
        self.active_task = task
        self.is_thinking = True
        
        # Save state
        self.save_tasks()
        
        return True
    
    def complete_active_task(self, result: Any = None) -> Optional[ThinkingTask]:
        """Complete the active thinking task with optional result"""
        if not self.active_task:
            return None
            
        self.active_task.complete(result)
        completed_task = self.active_task
        self.completed_tasks[completed_task.task_id] = completed_task
        self.active_task = None
        self.is_thinking = False
        
        # Save state
        self.save_tasks()
        
        return completed_task
    
    def fail_active_task(self, reason: str) -> Optional[ThinkingTask]:
        """Mark the active task as failed"""
        if not self.active_task:
            return None
            
        self.active_task.status = "failed"
        self.active_task.add_note(f"Failed: {reason}")
        failed_task = self.active_task
        self.failed_tasks[failed_task.task_id] = failed_task
        self.active_task = None
        self.is_thinking = False
        
        # Save state
        self.save_tasks()
        
        return failed_task
    
    def update_task_progress(self, progress: float, time_increment: float, note: str = None) -> bool:
        """Update progress on the active thinking task"""
        if not self.active_task:
            return False
            
        self.active_task.update_progress(progress, time_increment, note)
        
        # Check if task completed
        if self.active_task.status == "completed":
            self.completed_tasks[self.active_task.task_id] = self.active_task
            self.active_task = None
            self.is_thinking = False
        
        # Check if task should timeout
        elif self.active_task.should_timeout():
            self.fail_active_task("Exceeded maximum duration")
        
        # Save state
        self.save_tasks()
        
        return True
    
    def get_next_pending_task(self) -> Optional[ThinkingTask]:
        """Get the highest priority pending task"""
        if not self.pending_tasks:
            return None
            
        # Return highest priority task
        return max(self.pending_tasks.values(), key=lambda t: t.priority)
    
    def record_user_interaction(self):
        """Record that the user has interacted with the system"""
        self.user_present = True
        self.last_interaction_time = time.time()
        
        # If we're thinking and the task is interruptible, pause it
        if self.is_thinking and self.active_task and self.active_task.interruptible:
            self.active_task.interrupt()
            self.is_thinking = False
    
    def check_user_idle(self) -> bool:
        """Check if the user is idle based on last interaction time"""
        current_time = time.time()
        idle_time = current_time - self.last_interaction_time
        
        if idle_time > self.idle_threshold:
            self.user_present = False
            return True
        else:
            self.user_present = True
            return False
    
    def start_thinking_thread(self):
        """Start the background thinking thread"""
        if self.thinking_thread and self.thinking_thread.is_alive():
            return  # Thread already running
            
        self.stop_thinking.clear()
        self.thinking_thread = threading.Thread(target=self._thinking_process, daemon=True)
        self.thinking_thread.start()
        logger.info("Started extended thinking thread")
    
    def stop_thinking_thread(self):
        """Stop the background thinking thread"""
        if self.thinking_thread and self.thinking_thread.is_alive():
            self.stop_thinking.set()
            self.thinking_thread.join(timeout=2.0)
            logger.info("Stopped extended thinking thread")
    
    def _thinking_process(self):
        """Background thinking process"""
        logger.info("Extended thinking process started")
        
        while not self.stop_thinking.is_set():
            try:
                # Check if user is idle
                if not self.user_present and self.check_user_idle():
                    # User is idle, we can think
                    
                    # If we have an interrupted task, resume it
                    if self.active_task and self.active_task.status == "interrupted":
                        self.active_task.resume()
                        self.is_thinking = True
                        logger.info(f"Resumed interrupted thinking task: {self.active_task.description}")
                    
                    # If no active task, get the next pending task
                    elif not self.active_task:
                        next_task = self.get_next_pending_task()
                        if next_task:
                            self.start_task(next_task.task_id)
                            logger.info(f"Started new thinking task: {next_task.description}")
                    
                    # If we have an active task, make progress on it
                    if self.active_task and self.is_thinking:
                        # Simulate making progress
                        current_progress = self.active_task.progress
                        time_increment = 1.0  # 1 second of thinking
                        progress_increment = random.uniform(0.01, 0.05)  # Random progress
                        new_progress = min(1.0, current_progress + progress_increment)
                        
                        # Generate a thinking note (would be LLM output in real implementation)
                        thinking_note = None
                        if random.random() < 0.2:  # 20% chance to generate a note
                            thinking_note = f"Thinking about {self.active_task.description}..."
                            
                        # Update progress
                        self.update_task_progress(new_progress, time_increment, thinking_note)
                        
                # User is present, don't think actively
                else:
                    # If we're thinking, pause the task
                    if self.is_thinking and self.active_task:
                        self.active_task.interrupt()
                        self.is_thinking = False
                        logger.info(f"Interrupted thinking task due to user presence")
                
                # Sleep a bit to avoid hammering the CPU
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error in thinking process: {e}")
                time.sleep(5.0)  # Sleep longer on error
    
    def load_tasks(self) -> bool:
        """Load tasks from file"""
        if not os.path.exists(self.save_path):
            return False
            
        try:
            with open(self.save_path, 'r') as f:
                data = json.load(f)
                
            # Clear existing tasks
            self.pending_tasks = {}
            self.completed_tasks = {}
            self.failed_tasks = {}
            self.active_task = None
            
            # Load pending tasks
            for task_data in data.get("pending_tasks", []):
                task = ThinkingTask.from_dict(task_data)
                self.pending_tasks[task.task_id] = task
                
            # Load active task
            if data.get("active_task"):
                self.active_task = ThinkingTask.from_dict(data["active_task"])
                # On restart, interrupted active tasks
                if self.active_task.status == "in_progress":
                    self.active_task.interrupt()
                
            # Load completed tasks
            for task_data in data.get("completed_tasks", []):
                task = ThinkingTask.from_dict(task_data)
                self.completed_tasks[task.task_id] = task
                
            # Load failed tasks
            for task_data in data.get("failed_tasks", []):
                task = ThinkingTask.from_dict(task_data)
                self.failed_tasks[task.task_id] = task
                
            return True
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            return False
    
    def save_tasks(self) -> bool:
        """Save tasks to file"""
        try:
            data = {
                "pending_tasks": [task.to_dict() for task in self.pending_tasks.values()],
                "active_task": self.active_task.to_dict() if self.active_task else None,
                "completed_tasks": [task.to_dict() for task in self.completed_tasks.values()],
                "failed_tasks": [task.to_dict() for task in self.failed_tasks.values()]
            }
            
            with open(self.save_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            return True
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")
            return False

class LLMThinkingInterface:
    """
    Interface for using LLMs to perform thinking tasks
    Uses either the core model or the best available model
    """
    
    def __init__(self, model_manager=None):
        self.model_manager = model_manager
        self.fallback_llm = None
        
        # Try to get the fallback LLM (core model)
        try:
            from modules.fallback_llm import get_instance as get_fallback_llm
            self.fallback_llm = get_fallback_llm()
            self.has_core_model = True
        except ImportError:
            logger.warning("Core thinking model (fallback LLM) not available")
            self.has_core_model = False
    
    def perform_thinking(self, task: ThinkingTask) -> Dict[str, Any]:
        """
        Perform a thinking task using an LLM
        
        Args:
            task: The thinking task to perform
            
        Returns:
            Dict with thinking results and metadata
        """
        # Create a prompt based on the task type
        prompt = self._create_thinking_prompt(task)
        
        # Determine which model to use
        model_to_use = self._select_best_model(task)
        if not model_to_use:
            return {
                "success": False,
                "result": "No suitable thinking model available",
                "model_used": None
            }
        
        try:
            # Generate thinking output
            start_time = time.time()
            
            # Different interfaces based on model source
            if model_to_use == "model_manager" and self.model_manager:
                active_model = self.model_manager.get_active_model()
                thinking_output = active_model.generate_text(prompt, max_tokens=2048)
                model_name = active_model.model_name
            elif model_to_use == "core" and self.fallback_llm:
                thinking_output = self.fallback_llm.generate_text(prompt, max_tokens=800)
                model_name = self.fallback_llm.model_path
            else:
                return {
                    "success": False,
                    "result": "Selected model not available",
                    "model_used": model_to_use
                }
                
            end_time = time.time()
            
            # Process thinking output
            result = {
                "success": True,
                "result": thinking_output,
                "thinking_time": end_time - start_time,
                "model_used": model_name
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error during thinking task: {e}")
            return {
                "success": False,
                "result": f"Error during thinking: {str(e)}",
                "model_used": model_to_use
            }
    
    def _select_best_model(self, task: ThinkingTask) -> str:
        """
        Select the best model for the thinking task
        
        Args:
            task: The thinking task to perform
            
        Returns:
            String indicating which model to use ("model_manager", "core", or None)
        """
        # Determine task complexity and requirements
        is_complex = task.max_duration > 300 or "complex" in task.tags
        
        # Check if we have a model manager with an active model
        has_manager_model = (self.model_manager is not None and 
                            hasattr(self.model_manager, 'get_active_model') and 
                            self.model_manager.get_active_model() is not None)
        
        # Use the best available model for complex tasks
        if is_complex and has_manager_model:
            return "model_manager"
        
        # Use core model as default if available
        if self.has_core_model:
            return "core"
            
        # Fallback to model manager if core not available
        if has_manager_model:
            return "model_manager"
            
        # No suitable model available
        return None
    
    def _create_thinking_prompt(self, task: ThinkingTask) -> str:
        """
        Create a prompt for the thinking task
        
        Args:
            task: The thinking task to perform
            
        Returns:
            Formatted prompt for the LLM
        """
        # Base prompt based on task type
        if task.task_type == "reflection":
            base_prompt = "Perform a deep reflection on the following topic:"
        elif task.task_type == "concept_exploration":
            base_prompt = "Explore the concept in depth, considering different angles and implications:"
        elif task.task_type == "problem_solving":
            base_prompt = "Solve the following problem step by step, considering multiple approaches:"
        elif task.task_type == "creative_ideation":
            base_prompt = "Generate creative ideas and possibilities related to:"
        elif task.task_type == "goal_planning":
            base_prompt = "Develop a detailed plan to achieve the following goal:"
        else:
            base_prompt = "Think deeply about the following topic:"
        
        # Add task description
        prompt = f"{base_prompt}\n\n{task.description}\n\n"
        
        # Add thinking instructions
        prompt += """
Your task is to engage in extended thinking on this topic. Please:

1. Consider multiple perspectives and angles
2. Analyze deeply, making connections between ideas
3. Note any insights, patterns, or realizations along the way
4. Organize your thoughts into a coherent structure
5. Provide a thoughtful conclusion

Take your time with this thinking process.
"""
        
        # Add any existing notes as context
        if task.notes:
            prompt += "\n\nPrevious thinking notes:\n"
            for note in task.notes[-3:]:  # Include just the last 3 notes to avoid context overload
                prompt += f"- {note['content']}\n"

        # Add specific instructions based on progress
        if task.progress < 0.3:
            prompt += "\nYou're in the early stages of this thinking task. Focus on exploration and generating initial ideas."
        elif task.progress < 0.7:
            prompt += "\nYou're in the middle of this thinking task. Develop your ideas further and make connections."
        else:
            prompt += "\nYou're nearing completion of this thinking task. Focus on synthesizing your thoughts and forming conclusions."
        
        return prompt

class ExtendedThinking:
    """Main class for extended thinking capabilities"""
    
    def __init__(self):
        self.task_manager = ThinkingTaskManager()
        self.llm_interface = LLMThinkingInterface()
        self.enabled = True
        
        # Start thinking thread
        self.task_manager.start_thinking_thread()
    
    def connect_model_manager(self, model_manager):
        """Connect a model manager for enhanced thinking"""
        self.llm_interface.model_manager = model_manager
        logger.info("Connected model manager to extended thinking")
    
    def create_thinking_task(self, description: str, task_type: str = "reflection", 
                           priority: float = 0.5, max_duration: int = 600) -> str:
        """
        Create a new thinking task
        
        Args:
            description: What to think about
            task_type: Type of thinking to perform
            priority: Priority of the task (0.0 to 1.0)
            max_duration: Maximum duration in seconds
            
        Returns:
            Task ID if successful, otherwise None
        """
        if not self.enabled:
            return None
            
        task = self.task_manager.create_task(
            task_type=task_type,
            description=description,
            priority=priority,
            max_duration=max_duration
        )
        
        logger.info(f"Created thinking task: {task.description} (ID: {task.task_id})")
        return task.task_id
    
    def get_thinking_state(self) -> Dict[str, Any]:
        """Get the current state of thinking activities"""
        active_task = None
        if self.task_manager.active_task:
            active_task = {
                "task_id": self.task_manager.active_task.task_id,
                "description": self.task_manager.active_task.description,
                "type": self.task_manager.active_task.task_type,
                "progress": self.task_manager.active_task.progress,
                "status": self.task_manager.active_task.status
            }
            
        return {
            "enabled": self.enabled,
            "is_thinking": self.task_manager.is_thinking,
            "user_present": self.task_manager.user_present,
            "active_task": active_task,
            "pending_tasks": len(self.task_manager.pending_tasks),
            "completed_tasks": len(self.task_manager.completed_tasks)
        }
    
    def get_thinking_results(self, task_id: str) -> Dict[str, Any]:
        """Get the results of a thinking task"""
        task = self.task_manager.get_task(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
            
        return {
            "task_id": task.task_id,
            "description": task.description,
            "type": task.task_type,
            "status": task.status,
            "progress": task.progress,
            "time_spent": task.time_spent,
            "created_at": task.created_at,
            "completed_at": task.completed_at,
            "result": task.result,
            "notes": [note["content"] for note in task.notes],
            "success": task.status == "completed"
        }
    
    def perform_immediate_thinking(self, description: str, task_type: str = "reflection", 
                                 max_duration: int = 60) -> Dict[str, Any]:
        """
        Perform immediate thinking on a topic (blocking)
        
        Args:
            description: What to think about
            task_type: Type of thinking to perform
            max_duration: Maximum duration in seconds
            
        Returns:
            Dict with thinking results
        """
        if not self.enabled:
            return {"success": False, "error": "Extended thinking is disabled"}
            
        # Create a temporary task
        task = ThinkingTask(
            task_id=f"immediate_{int(time.time())}",
            task_type=task_type,
            description=description,
            max_duration=max_duration
        )
        
        # Perform thinking
        thinking_result = self.llm_interface.perform_thinking(task)
        
        # If successful, store the task
        if thinking_result["success"]:
            task.complete(thinking_result["result"])
            self.task_manager.completed_tasks[task.task_id] = task
            self.task_manager.save_tasks()
            
        return thinking_result
    
    def enable(self):
        """Enable extended thinking"""
        self.enabled = True
        self.task_manager.start_thinking_thread()
        logger.info("Extended thinking enabled")
        
    def disable(self):
        """Disable extended thinking"""
        self.enabled = False
        self.task_manager.stop_thinking_thread()
        logger.info("Extended thinking disabled")
        
    def record_user_interaction(self):
        """Record that the user has interacted with the system"""
        self.task_manager.record_user_interaction()
        
    def cleanup(self):
        """Clean up resources before shutdown"""
        self.task_manager.stop_thinking_thread()
        self.task_manager.save_tasks()

# Singleton instance
_instance = None

def get_instance():
    """Get the singleton instance of ExtendedThinking"""
    global _instance
    if _instance is None:
        _instance = ExtendedThinking()
    return _instance
