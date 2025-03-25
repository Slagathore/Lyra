"""
State preservation and recovery system for Lyra
Allows components to save and restore their state
"""

import os
import json
import time
import logging
import threading
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable

# Set up logging
logger = logging.getLogger("state_manager")

class StateManager:
    """
    Manages state preservation and recovery for Lyra components
    Provides automatic backup and restoration of component state
    """
    
    def __init__(self, data_dir: str = "data/state"):
        """
        Initialize the state manager
        
        Args:
            data_dir: Directory for state storage
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        
        # Track registered components
        self.components = {}
        
        # Auto-save timer
        self.autosave_interval = 300  # 5 minutes
        self.autosave_timer = None
        self.autosave_running = False
        
        # Thread lock for saving/loading operations
        self.lock = threading.RLock()
    
    def register_component(self, component_id: str, 
                         get_state_func: Callable[[], Dict[str, Any]],
                         set_state_func: Callable[[Dict[str, Any]], bool] = None):
        """
        Register a component for state management
        
        Args:
            component_id: Unique identifier for the component
            get_state_func: Function that returns the component's state
            set_state_func: Function that sets the component's state
        """
        with self.lock:
            self.components[component_id] = {
                "id": component_id,
                "get_state": get_state_func,
                "set_state": set_state_func,
                "last_save_time": 0,
                "save_count": 0
            }
            logger.info(f"Registered component for state management: {component_id}")
    
    def save_state(self, component_id: str = None) -> bool:
        """
        Save the state of a component or all components
        
        Args:
            component_id: Optional component ID (saves all if None)
            
        Returns:
            True if state was saved successfully
        """
        with self.lock:
            if component_id is not None:
                # Save a specific component
                if component_id not in self.components:
                    logger.warning(f"Component not registered: {component_id}")
                    return False
                
                return self._save_component_state(component_id)
            else:
                # Save all components
                success = True
                for comp_id in self.components:
                    if not self._save_component_state(comp_id):
                        success = False
                
                return success
    
    def _save_component_state(self, component_id: str) -> bool:
        """
        Save the state of a specific component
        
        Args:
            component_id: Component ID to save
            
        Returns:
            True if state was saved successfully
        """
        component = self.components[component_id]
        
        try:
            # Get the component's state
            state = component["get_state"]()
            
            if not state:
                logger.warning(f"Empty state returned for component: {component_id}")
                return False
            
            # Add metadata
            state_with_meta = {
                "component_id": component_id,
                "timestamp": time.time(),
                "version": "1.0",
                "state": state
            }
            
            # Determine file paths
            state_file = self.data_dir / f"{component_id}.json"
            backup_file = self.data_dir / f"{component_id}.backup.json"
            
            # If current state file exists, make a backup
            if state_file.exists():
                if backup_file.exists():
                    backup_file.unlink()
                state_file.rename(backup_file)
            
            # Save the new state
            with open(state_file, 'w') as f:
                json.dump(state_with_meta, f, indent=2)
            
            # Update component metadata
            component["last_save_time"] = time.time()
            component["save_count"] += 1
            
            logger.info(f"State saved for component: {component_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving state for component {component_id}: {e}")
            return False
    
    def load_state(self, component_id: str) -> bool:
        """
        Load the state of a component
        
        Args:
            component_id: Component ID to load
            
        Returns:
            True if state was loaded successfully
        """
        with self.lock:
            if component_id not in self.components:
                logger.warning(f"Component not registered: {component_id}")
                return False
            
            component = self.components[component_id]
            
            if component["set_state"] is None:
                logger.warning(f"Component {component_id} does not support state loading")
                return False
            
            # Check for state file
            state_file = self.data_dir / f"{component_id}.json"
            backup_file = self.data_dir / f"{component_id}.backup.json"
            
            if not state_file.exists():
                if not backup_file.exists():
                    logger.warning(f"No state file found for component: {component_id}")
                    return False
                
                # Use backup file if main file doesn't exist
                state_file = backup_file
            
            try:
                # Load the state
                with open(state_file, 'r') as f:
                    state_with_meta = json.load(f)
                
                # Extract the actual state
                state = state_with_meta.get("state", {})
                
                # Set the component's state
                result = component["set_state"](state)
                
                if result:
                    logger.info(f"State loaded for component: {component_id}")
                else:
                    logger.warning(f"Component {component_id} rejected state")
                
                return result
            
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in state file for component: {component_id}")
                
                # Try to use backup
                if state_file != backup_file and backup_file.exists():
                    logger.info(f"Trying backup file for component: {component_id}")
                    try:
                        with open(backup_file, 'r') as f:
                            state_with_meta = json.load(f)
                        
                        state = state_with_meta.get("state", {})
                        result = component["set_state"](state)
                        
                        if result:
                            logger.info(f"State loaded from backup for component: {component_id}")
                        else:
                            logger.warning(f"Component {component_id} rejected backup state")
                        
                        return result
                    except:
                        logger.error(f"Error loading backup state for component: {component_id}")
                
                return False
            
            except Exception as e:
                logger.error(f"Error loading state for component {component_id}: {e}")
                return False
    
    def start_autosave(self, interval: int = None):
        """
        Start automatic periodic state saving
        
        Args:
            interval: Save interval in seconds (default: 5 minutes)
        """
        with self.lock:
            if self.autosave_running:
                logger.warning("Autosave is already running")
                return
            
            if interval is not None:
                self.autosave_interval = interval
            
            self.autosave_running = True
            self._schedule_autosave()
            
            logger.info(f"Autosave started with interval: {self.autosave_interval} seconds")
    
    def stop_autosave(self):
        """Stop automatic state saving"""
        with self.lock:
            self.autosave_running = False
            
            if self.autosave_timer:
                self.autosave_timer.cancel()
                self.autosave_timer = None
            
            logger.info("Autosave stopped")
    
    def _schedule_autosave(self):
        """Schedule the next autosave"""
        if not self.autosave_running:
            return
        
        self.autosave_timer = threading.Timer(self.autosave_interval, self._run_autosave)
        self.autosave_timer.daemon = True
        self.autosave_timer.start()
    
    def _run_autosave(self):
        """Run autosave and reschedule"""
        try:
            logger.debug("Running autosave")
            self.save_state()
        except Exception as e:
            logger.error(f"Error during autosave: {e}")
        finally:
            # Reschedule next autosave
            self._schedule_autosave()
    
    def get_state_info(self) -> Dict[str, Any]:
        """
        Get information about saved states
        
        Returns:
            Dictionary with state information
        """
        info = {
            "components": {},
            "autosave": {
                "running": self.autosave_running,
                "interval": self.autosave_interval
            }
        }
        
        # Get info for each component
        for comp_id, component in self.components.items():
            state_file = self.data_dir / f"{comp_id}.json"
            backup_file = self.data_dir / f"{comp_id}.backup.json"
            
            info["components"][comp_id] = {
                "registered": True,
                "state_file_exists": state_file.exists(),
                "backup_file_exists": backup_file.exists(),
                "last_save_time": component["last_save_time"],
                "save_count": component["save_count"],
                "supports_loading": component["set_state"] is not None
            }
            
            # Add state file details if it exists
            if state_file.exists():
                try:
                    info["components"][comp_id]["state_file_size"] = state_file.stat().st_size
                    info["components"][comp_id]["state_file_modified"] = state_file.stat().st_mtime
                except:
                    pass
        
        return info

# Singleton instance
_state_manager = None

def get_state_manager() -> StateManager:
    """
    Get the singleton state manager instance
    
    Returns:
        StateManager instance
    """
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager

def register_component(component_id: str, 
                      get_state_func: Callable[[], Dict[str, Any]],
                      set_state_func: Callable[[Dict[str, Any]], bool] = None):
    """
    Register a component for state management
    
    Args:
        component_id: Unique identifier for the component
        get_state_func: Function that returns the component's state
        set_state_func: Function that sets the component's state
    """
    sm = get_state_manager()
    sm.register_component(component_id, get_state_func, set_state_func)

def save_component_state(component_id: str) -> bool:
    """
    Save state for a specific component
    
    Args:
        component_id: Component ID to save
        
    Returns:
        True if successful
    """
    sm = get_state_manager()
    return sm.save_state(component_id)

def load_component_state(component_id: str) -> bool:
    """
    Load state for a specific component
    
    Args:
        component_id: Component ID to load
        
    Returns:
        True if successful
    """
    sm = get_state_manager()
    return sm.load_state(component_id)

def start_autosave(interval: int = None):
    """Start automatic state saving"""
    sm = get_state_manager()
    sm.start_autosave(interval)

def stop_autosave():
    """Stop automatic state saving"""
    sm = get_state_manager()
    sm.stop_autosave()
