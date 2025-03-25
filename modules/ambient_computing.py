import os
import time
import json
import logging
import queue
import random
import threading
import asyncio
from typing import Dict, Any, Callable, List, Optional

logger = logging.getLogger(__name__)

class Thought:
    def __init__(self, id: str, query: str, priority: int = 1, category: str = "general"):
        self.id = id
        self.query = query
        self.priority = priority
        self.category = category
        self.status = "pending"
        self.result = None
        self.error = None
        self.created_at = time.time()
        self.completed_at = None
        self.processing_time = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "query": self.query,
            "priority": self.priority,
            "category": self.category,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "processing_time": self.processing_time
        }

class AmbientProcessor:
    def __init__(self):
        self.enabled = False
        self.listen_mode = False
        self.context = {}
        self.thought_queue = queue.PriorityQueue()
        self.active_thoughts = {}
        self.thought_history = []
        self.max_pending_thoughts = 100
        self.max_thought_history = 1000
        self.max_workers = 5
        self.thought_timeout = 60  # seconds
        self.save_interval = 300  # seconds
        self.last_save = time.time()
        self.model_callback = None
        self.action_callback = None
        self.update_callback = None
        self.executor = threading.Thread(target=self._run_event_loop, daemon=True)
        self.should_run = True
        self.executor.start()

    def enable(self, state: bool = True) -> bool:
        self.enabled = state
        self.save_settings()
        return self.enabled

    def save_settings(self):
        try:
            settings = {
                "enabled": self.enabled,
                "listen_mode": self.listen_mode,
                "context": self.context
            }
            settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ambient_settings.json")
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            logger.info("Saved ambient processor settings")
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")

    def load_settings(self):
        try:
            settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ambient_settings.json")
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                self.enabled = settings.get("enabled", False)
                self.listen_mode = settings.get("listen_mode", False)
                self.context = settings.get("context", {})
                logger.info("Loaded ambient processor settings")
        except Exception as e:
            logger.error(f"Error loading settings: {str(e)}")

    def set_listen_mode(self, enabled: bool = True) -> bool:
        self.listen_mode = enabled
        self.save_settings()
        return self.listen_mode

    def set_callback(self, callback_type: str, callback_func: Callable) -> bool:
        try:
            if callback_type == "model":
                self.model_callback = callback_func
            elif callback_type == "action":
                self.action_callback = callback_func
            elif callback_type == "update":
                self.update_callback = callback_func
            else:
                logger.warning(f"Unknown callback type: {callback_type}")
                return False
            return True
        except Exception as e:
            logger.error(f"Error setting callback: {str(e)}")
            return False

    def _run_event_loop(self):
        try:
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
            while self.should_run:
                self._process_thoughts()
                self._update_active_thoughts()
                if self.listen_mode:
                    self._check_ambient_triggers()
                current_time = time.time()
                if current_time - self.last_save > self.save_interval:
                    self.save_state()
                time.sleep(0.1)
            if self.event_loop and self.event_loop.is_running():
                self.event_loop.stop()
        except Exception as e:
            logger.error(f"Error in ambient processor event loop: {str(e)}")

    def _process_thoughts(self):
        try:
            if len(self.active_thoughts) >= self.max_workers:
                return
            try:
                priority, thought = self.thought_queue.get(block=False)
                self._start_thought_processing(thought)
            except queue.Empty:
                pass
        except Exception as e:
            logger.error(f"Error processing thoughts: {str(e)}")

    def _start_thought_processing(self, thought: Thought):
        try:
            thought.status = "processing"
            self.active_thoughts[thought.id] = thought
            future = self.executor.submit(self._process_thought, thought)
            future.add_done_callback(lambda f: self._thought_completed(thought.id, f))
        except Exception as e:
            logger.error(f"Error starting thought processing: {str(e)}")
            thought.status = "failed"
            thought.error = str(e)
            self.thought_history.append(thought)
            if thought.id in self.active_thoughts:
                del self.active_thoughts[thought.id]

    def _process_thought(self, thought: Thought) -> Any:
        start_time = time.time()
        try:
            if self.model_callback:
                result = self.model_callback(thought.query, thought.category)
                thought.processing_time = time.time() - start_time
                return result
            else:
                raise Exception("No model callback registered")
        except Exception as e:
            logger.error(f"Error processing thought {thought.id}: {str(e)}")
            raise

    def _thought_completed(self, thought_id: str, future):
        try:
            thought = self.active_thoughts.get(thought_id)
            if not thought:
                return
            try:
                result = future.result()
                thought.status = "completed"
                thought.result = result
                thought.completed_at = time.time()
                if self.action_callback:
                    self.action_callback(thought)
            except Exception as e:
                thought.status = "failed"
                thought.error = str(e)
                logger.error(f"Thought processing failed: {str(e)}")
            self.thought_history.append(thought)
            del self.active_thoughts[thought_id]
            if len(self.thought_history) > self.max_thought_history:
                self.thought_history = self.thought_history[-self.max_thought_history:]
            if self.update_callback:
                self.update_callback(thought)
        except Exception as e:
            logger.error(f"Error handling completed thought: {str(e)}")

    def _update_active_thoughts(self):
        try:
            current_time = time.time()
            timed_out_ids = []
            for thought_id, thought in self.active_thoughts.items():
                if thought.status == "processing" and (current_time - thought.created_at) > self.thought_timeout:
                    timed_out_ids.append(thought_id)
            for thought_id in timed_out_ids:
                thought = self.active_thoughts[thought_id]
                thought.status = "failed"
                thought.error = "Thought processing timed out"
                self.thought_history.append(thought)
                del self.active_thoughts[thought_id]
                logger.warning(f"Thought {thought_id} timed out after {self.thought_timeout} seconds")
        except Exception as e:
            logger.error(f"Error updating active thoughts: {str(e)}")

    def _check_ambient_triggers(self):
        try:
            if "last_interaction_time" in self.context:
                seconds_since_interaction = time.time() - self.context["last_interaction_time"]
                if seconds_since_interaction < 60:
                    if random.random() < 0.05 and "last_topic" in self.context:
                        self.add_thought(
                            query=f"What might be interesting to say about {self.context['last_topic']}?",
                            category="ambient_suggestion",
                            priority=3
                        )
            if "next_calendar_event" in self.context:
                event = self.context["next_calendar_event"]
                if "start_time" in event:
                    minutes_until = (event["start_time"] - time.time()) / 60
                    if 10 <= minutes_until <= 15:
                        self.add_thought(
                            query=f"Reminder about upcoming event: {event['title']}",
                            category="reminder",
                            priority=5
                        )
        except Exception as e:
            logger.error(f"Error checking ambient triggers: {str(e)}")

    def add_thought(self, query: str, category: str = "general", priority: int = 1) -> str:
        try:
            if not self.enabled:
                logger.warning("Ambient processor is disabled, not adding thought")
                return ""
            if self.thought_queue.qsize() >= self.max_pending_thoughts:
                logger.warning("Thought queue is full, not adding thought")
                return ""
            thought_id = f"thought_{int(time.time())}_{random.randint(1000, 9999)}"
            thought = Thought(
                id=thought_id,
                query=query,
                priority=priority,
                category=category
            )
            self.thought_queue.put((10 - priority, thought))
            return thought_id
        except Exception as e:
            logger.error(f"Error adding thought: {str(e)}")
            return ""

    def get_thought(self, thought_id: str) -> Optional[Dict[str, Any]]:
        try:
            if thought_id in self.active_thoughts:
                return self.active_thoughts[thought_id].to_dict()
            for thought in self.thought_history:
                if thought.id == thought_id:
                    return thought.to_dict()
            return None
        except Exception as e:
            logger.error(f"Error getting thought: {str(e)}")
            return None

    def get_active_thoughts(self) -> List[Dict[str, Any]]:
        try:
            return [thought.to_dict() for thought in self.active_thoughts.values()]
        except Exception as e:
            logger.error(f"Error getting active thoughts: {str(e)}")
            return []

    def get_thought_history(self, category: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            if category:
                filtered = [t for t in self.thought_history if t.category == category]
            else:
                filtered = self.thought_history
            sorted_thoughts = sorted(filtered, key=lambda t: t.created_at, reverse=True)
            limited = sorted_thoughts[:limit]
            return [thought.to_dict() for thought in limited]
        except Exception as e:
            logger.error(f"Error getting thought history: {str(e)}")
            return []

    def update_context(self, context_updates: Dict[str, Any]) -> bool:
        try:
            self.context.update(context_updates)
            return True
        except Exception as e:
            logger.error(f"Error updating context: {str(e)}")
            return False

    def get_context(self) -> Dict[str, Any]:
        return self.context.copy()

    def clear_thoughts(self) -> bool:
        try:
            self.active_thoughts = {}
            self.thought_history = []
            while not self.thought_queue.empty():
                try:
                    self.thought_queue.get_nowait()
                except queue.Empty:
                    break
            return True
        except Exception as e:
            logger.error(f"Error clearing thoughts: {str(e)}")
            return False

class ParallelThoughtProcessor:
    def __init__(self, max_concurrent=3):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_tasks = {}

    async def process_thought_async(self, thought_id: str, query: str, 
                                 process_func: Callable[[str], Coroutine[Any, Any, Any]]) -> Any:
        async with self.semaphore:
            task = asyncio.current_task()
            self.active_tasks[thought_id] = task
            try:
                result = await process_func(query)
                return result
            finally:
                if thought_id in self.active_tasks:
                    del self.active_tasks[thought_id]

    def cancel_thought(self, thought_id: str) -> bool:
        if thought_id in self.active_tasks:
            task = self.active_tasks[thought_id]
            task.cancel()
            del self.active_tasks[thought_id]
            return True
        return False

    async def cancel_all(self):
        for task in self.active_tasks.values():
            task.cancel()
        self.active_tasks = {}

# Global instance
_ambient_processor = None

def get_ambient_processor():
    global _ambient_processor
    if _ambient_processor is None:
        _ambient_processor = AmbientProcessor()
    return _ambient_processor