"""
Health monitoring system for Lyra
Tracks system health, resource usage, and component status
"""

import os
import time
import logging
import threading
import platform
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

# Set up logging
logger = logging.getLogger("health_monitor")

# Try to import psutil for system resource monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    logger.warning("psutil not available, system resource monitoring will be limited")
    PSUTIL_AVAILABLE = False

class HealthMonitor:
    """
    Monitors the health and performance of the Lyra system
    Collects metrics and generates health reports
    """
    
    def __init__(self, data_dir: str = "data/health"):
        """
        Initialize the health monitor
        
        Args:
            data_dir: Directory for health data storage
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        
        # Monitoring state
        self.monitoring = False
        self.monitor_thread = None
        self.monitor_interval = 60  # 1 minute by default
        
        # System resources thresholds
        self.thresholds = {
            "cpu_percent": 80.0,  # Warn if CPU usage > 80%
            "memory_percent": 85.0,  # Warn if memory usage > 85%
            "disk_percent": 90.0,  # Warn if disk usage > 90%
            "component_response_time": 5.0  # Warn if component takes > 5s to respond
        }
        
        # Registered components
        self.components = {}
        
        # Metrics history
        self.metrics_history = {
            "system": [],
            "components": {}
        }
        
        # Max history entries (per component)
        self.max_history = 60  # 1 hour at 1 minute intervals
        
        # Alert callbacks
        self.alert_callbacks = []
    
    def register_component(self, component_id: str, 
                         health_check_func: Callable[[], Dict[str, Any]] = None):
        """
        Register a component for health monitoring
        
        Args:
            component_id: Unique identifier for the component
            health_check_func: Function that returns component health data
        """
        self.components[component_id] = {
            "id": component_id,
            "health_check": health_check_func,
            "last_check_time": 0,
            "last_status": None,
            "alert_count": 0
        }
        
        # Initialize metrics history for this component
        if component_id not in self.metrics_history["components"]:
            self.metrics_history["components"][component_id] = []
        
        logger.info(f"Registered component for health monitoring: {component_id}")
    
    def register_alert_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """
        Register a callback for health alerts
        
        Args:
            callback: Function that receives (alert_type, alert_data)
        """
        self.alert_callbacks.append(callback)
    
    def start_monitoring(self, interval: int = None):
        """
        Start health monitoring
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self.monitoring:
            logger.warning("Health monitoring is already running")
            return
        
        if interval is not None:
            self.monitor_interval = interval
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info(f"Health monitoring started with interval: {self.monitor_interval} seconds")
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        if not self.monitoring:
            logger.warning("Health monitoring is not running")
            return
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
            self.monitor_thread = None
        
        logger.info("Health monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Check system resources
                system_health = self.check_system_health()
                
                # Check component health
                component_health = self.check_components_health()
                
                # Combine into overall health status
                health_status = {
                    "timestamp": time.time(),
                    "system": system_health,
                    "components": component_health,
                    "overall_status": "healthy"  # Default to healthy
                }
                
                # Determine overall status based on individual statuses
                if system_health.get("status") == "warning" or any(comp.get("status") == "warning" for comp in component_health.values()):
                    health_status["overall_status"] = "warning"
                
                if system_health.get("status") == "critical" or any(comp.get("status") == "critical" for comp in component_health.values()):
                    health_status["overall_status"] = "critical"
                
                # Update metrics history
                self._update_metrics_history(health_status)
                
                # Check for alerts
                self._check_for_alerts(health_status)
                
                # Save status to file periodically (every 10 checks)
                if int(time.time()) % (self.monitor_interval * 10) < self.monitor_interval:
                    self._save_health_status(health_status)
                
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
            
            # Sleep until next check
            time.sleep(self.monitor_interval)
    
    def check_system_health(self) -> Dict[str, Any]:
        """
        Check system health metrics
        
        Returns:
            Dictionary with system health data
        """
        health_data = {
            "timestamp": time.time(),
            "status": "healthy",
            "cpu_percent": 0,
            "memory_percent": 0,
            "disk_percent": 0,
            "warnings": [],
            "platform": platform.platform(),
            "python_version": platform.python_version()
        }
        
        # Get system resources if psutil is available
        if PSUTIL_AVAILABLE:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=0.5)
                health_data["cpu_percent"] = cpu_percent
                
                if cpu_percent > self.thresholds["cpu_percent"]:
                    health_data["warnings"].append(f"High CPU usage: {cpu_percent:.1f}%")
                    health_data["status"] = "warning"
                
                # Memory usage
                memory = psutil.virtual_memory()
                health_data["memory_percent"] = memory.percent
                health_data["memory_available_mb"] = memory.available / (1024 * 1024)
                health_data["memory_total_mb"] = memory.total / (1024 * 1024)
                
                if memory.percent > self.thresholds["memory_percent"]:
                    health_data["warnings"].append(f"High memory usage: {memory.percent:.1f}%")
                    health_data["status"] = "warning"
                
                # Disk usage (for the system drive)
                disk = psutil.disk_usage("/")
                health_data["disk_percent"] = disk.percent
                health_data["disk_free_gb"] = disk.free / (1024 * 1024 * 1024)
                health_data["disk_total_gb"] = disk.total / (1024 * 1024 * 1024)
                
                if disk.percent > self.thresholds["disk_percent"]:
                    health_data["warnings"].append(f"Low disk space: {disk.percent:.1f}% used")
                    health_data["status"] = "warning"
                
                # Process info
                process = psutil.Process()
                health_data["process_memory_mb"] = process.memory_info().rss / (1024 * 1024)
                health_data["process_cpu_percent"] = process.cpu_percent(interval=0.1)
                health_data["process_create_time"] = process.create_time()
                health_data["process_uptime"] = time.time() - process.create_time()
                
                # Check for critical conditions
                if (cpu_percent > self.thresholds["cpu_percent"] * 1.2 or
                    memory.percent > self.thresholds["memory_percent"] * 1.2 or
                    disk.percent > self.thresholds["disk_percent"] * 1.1):
                    health_data["status"] = "critical"
                
            except Exception as e:
                logger.error(f"Error getting system resources: {e}")
                health_data["warnings"].append(f"Error monitoring system resources: {str(e)}")
        else:
            # Limited information without psutil
            health_data["warnings"].append("psutil not available, limited system monitoring")
            
            # Try to get process memory using resource module
            try:
                import resource
                rusage = resource.getrusage(resource.RUSAGE_SELF)
                health_data["process_memory_mb"] = rusage.ru_maxrss / 1024  # Convert KB to MB
            except ImportError:
                pass
        
        return health_data
    
    def check_components_health(self) -> Dict[str, Dict[str, Any]]:
        """
        Check health of all registered components
        
        Returns:
            Dictionary mapping component IDs to health data
        """
        results = {}
        
        for component_id, component in self.components.items():
            # Skip components without a health check function
            if not component["health_check"]:
                continue
            
            try:
                # Measure response time
                start_time = time.time()
                health_data = component["health_check"]()
                response_time = time.time() - start_time
                
                # Add response time to health data
                if isinstance(health_data, dict):
                    health_data["response_time"] = response_time
                    
                    # Add warning if response time is too long
                    if response_time > self.thresholds["component_response_time"]:
                        if "warnings" not in health_data:
                            health_data["warnings"] = []
                        health_data["warnings"].append(f"Slow response time: {response_time:.2f}s")
                        
                        if "status" not in health_data or health_data["status"] == "healthy":
                            health_data["status"] = "warning"
                else:
                    # If health check didn't return a dict, create one
                    health_data = {
                        "status": "unknown",
                        "raw_data": health_data,
                        "response_time": response_time
                    }
                
                # Add timestamp
                health_data["timestamp"] = time.time()
                
                # Store in results
                results[component_id] = health_data
                
                # Update component metadata
                component["last_check_time"] = time.time()
                component["last_status"] = health_data.get("status", "unknown")
                
            except Exception as e:
                logger.error(f"Error checking health for component {component_id}: {e}")
                
                # Record error in results
                results[component_id] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": time.time()
                }
                
                # Update component metadata
                component["last_check_time"] = time.time()
                component["last_status"] = "error"
                component["alert_count"] += 1
        
        return results
    
    def _update_metrics_history(self, health_status: Dict[str, Any]):
        """
        Update metrics history with new health data
        
        Args:
            health_status: Latest health status data
        """
        # Update system metrics history
        self.metrics_history["system"].append({
            "timestamp": health_status["timestamp"],
            "cpu_percent": health_status["system"].get("cpu_percent", 0),
            "memory_percent": health_status["system"].get("memory_percent", 0),
            "disk_percent": health_status["system"].get("disk_percent", 0),
            "status": health_status["system"].get("status", "unknown")
        })
        
        # Trim system history if needed
        if len(self.metrics_history["system"]) > self.max_history:
            self.metrics_history["system"] = self.metrics_history["system"][-self.max_history:]
        
        # Update component metrics history
        for component_id, component_data in health_status["components"].items():
            if component_id not in self.metrics_history["components"]:
                self.metrics_history["components"][component_id] = []
            
            # Extract key metrics depending on what's available
            metrics = {
                "timestamp": component_data.get("timestamp", health_status["timestamp"]),
                "status": component_data.get("status", "unknown"),
                "response_time": component_data.get("response_time", 0)
            }
            
            # Add any numeric metrics that might be present
            for key, value in component_data.items():
                if isinstance(value, (int, float)) and key not in metrics:
                    metrics[key] = value
            
            # Add to history
            self.metrics_history["components"][component_id].append(metrics)
            
            # Trim component history if needed
            if len(self.metrics_history["components"][component_id]) > self.max_history:
                self.metrics_history["components"][component_id] = self.metrics_history["components"][component_id][-self.max_history:]
    
    def _check_for_alerts(self, health_status: Dict[str, Any]):
        """
        Check for alert conditions in health status
        
        Args:
            health_status: Latest health status data
        """
        # System alerts
        if health_status["system"].get("status") == "critical":
            alert_data = {
                "type": "system_critical",
                "timestamp": time.time(),
                "message": "System resources critically low",
                "details": health_status["system"].get("warnings", [])
            }
            self._send_alert("system_critical", alert_data)
        
        elif health_status["system"].get("status") == "warning":
            alert_data = {
                "type": "system_warning",
                "timestamp": time.time(),
                "message": "System resource warning",
                "details": health_status["system"].get("warnings", [])
            }
            self._send_alert("system_warning", alert_data)
        
        # Component alerts
        for component_id, component_data in health_status["components"].items():
            if component_data.get("status") == "critical":
                alert_data = {
                    "type": "component_critical",
                    "component_id": component_id,
                    "timestamp": time.time(),
                    "message": f"Component {component_id} is in critical state",
                    "details": component_data.get("warnings", [])
                }
                self._send_alert("component_critical", alert_data)
            
            elif component_data.get("status") == "warning":
                alert_data = {
                    "type": "component_warning",
                    "component_id": component_id,
                    "timestamp": time.time(),
                    "message": f"Component {component_id} has warnings",
                    "details": component_data.get("warnings", [])
                }
                self._send_alert("component_warning", alert_data)
            
            elif component_data.get("status") == "error":
                alert_data = {
                    "type": "component_error",
                    "component_id": component_id,
                    "timestamp": time.time(),
                    "message": f"Component {component_id} encountered an error",
                    "details": [component_data.get("error", "Unknown error")]
                }
                self._send_alert("component_error", alert_data)
    
    def _send_alert(self, alert_type: str, alert_data: Dict[str, Any]):
        """
        Send an alert to all registered callbacks
        
        Args:
            alert_type: Type of alert
            alert_data: Alert data
        """
        logger.warning(f"Health alert: {alert_type} - {alert_data['message']}")
        
        # Log to alerts file
        self._log_alert(alert_type, alert_data)
        
        # Send to all callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert_type, alert_data)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def _log_alert(self, alert_type: str, alert_data: Dict[str, Any]):
        """
        Log an alert to the alerts file
        
        Args:
            alert_type: Type of alert
            alert_data: Alert data
        """
        alerts_file = self.data_dir / "alerts.log"
        
        try:
            with open(alerts_file, 'a') as f:
                timestamp = datetime.fromtimestamp(alert_data["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {alert_type}: {alert_data['message']}\n")
                
                # Write details if any
                for detail in alert_data.get("details", []):
                    f.write(f"  - {detail}\n")
                
                f.write("\n")
        except Exception as e:
            logger.error(f"Error logging alert: {e}")
    
    def _save_health_status(self, health_status: Dict[str, Any]):
        """
        Save full health status to a file
        
        Args:
            health_status: Health status data to save
        """
        timestamp = datetime.fromtimestamp(health_status["timestamp"]).strftime("%Y%m%d_%H%M%S")
        status_file = self.data_dir / f"health_status_{timestamp}.json"
        
        try:
            with open(status_file, 'w') as f:
                json.dump(health_status, f, indent=2)
            
            # Keep only the latest 10 status files
            status_files = sorted(self.data_dir.glob("health_status_*.json"))
            if len(status_files) > 10:
                for old_file in status_files[:-10]:
                    old_file.unlink()
        except Exception as e:
            logger.error(f"Error saving health status: {e}")
    
    def get_current_health(self) -> Dict[str, Any]:
        """
        Get current health status
        
        Returns:
            Dictionary with current health status
        """
        system_health = self.check_system_health()
        component_health = self.check_components_health()
        
        return {
            "timestamp": time.time(),
            "system": system_health,
            "components": component_health,
            "metrics_history": {
                "system_count": len(self.metrics_history["system"]),
                "component_counts": {comp_id: len(metrics) for comp_id, metrics in self.metrics_history["components"].items()}
            }
        }
    
    def get_health_report(self, include_history: bool = False) -> Dict[str, Any]:
        """
        Generate a health report
        
        Args:
            include_history: Whether to include metrics history
            
        Returns:
            Dictionary with health report data
        """
        # Get current health status
        current_health = self.get_current_health()
        
        # Create report
        report = {
            "timestamp": time.time(),
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_health": current_health,
            "components_registered": list(self.components.keys()),
            "monitoring_status": {
                "active": self.monitoring,
                "interval": self.monitor_interval
            },
            "thresholds": self.thresholds
        }
        
        # Add system summary
        if self.metrics_history["system"]:
            latest = self.metrics_history["system"][-1]
            oldest = self.metrics_history["system"][0] if self.metrics_history["system"] else latest
            
            report["system_summary"] = {
                "current_status": latest["status"],
                "cpu_current": latest["cpu_percent"],
                "memory_current": latest["memory_percent"],
                "disk_current": latest["disk_percent"],
                "cpu_average": sum(m["cpu_percent"] for m in self.metrics_history["system"]) / len(self.metrics_history["system"]),
                "memory_average": sum(m["memory_percent"] for m in self.metrics_history["system"]) / len(self.metrics_history["system"]),
                "monitoring_period": latest["timestamp"] - oldest["timestamp"]
            }
        
        # Add component summaries
        report["component_summaries"] = {}
        for comp_id, metrics in self.metrics_history["components"].items():
            if not metrics:
                continue
                
            latest = metrics[-1]
            oldest = metrics[0] if metrics else latest
            
            report["component_summaries"][comp_id] = {
                "current_status": latest["status"],
                "response_time_current": latest.get("response_time", 0),
                "response_time_average": sum(m.get("response_time", 0) for m in metrics) / len(metrics),
                "monitoring_period": latest["timestamp"] - oldest["timestamp"]
            }
        
        # Add history if requested
        if include_history:
            report["metrics_history"] = self.metrics_history
        
        return report

# Singleton instance
_health_monitor = None

def get_health_monitor() -> HealthMonitor:
    """
    Get the singleton health monitor instance
    
    Returns:
        HealthMonitor instance
    """
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor

def register_component(component_id: str, health_check_func: Callable[[], Dict[str, Any]] = None):
    """
    Register a component for health monitoring
    
    Args:
        component_id: Unique identifier for the component
        health_check_func: Function that returns component health data
    """
    hm = get_health_monitor()
    hm.register_component(component_id, health_check_func)

def start_monitoring(interval: int = None):
    """Start health monitoring"""
    hm = get_health_monitor()
    hm.start_monitoring(interval)

def stop_monitoring():
    """Stop health monitoring"""
    hm = get_health_monitor()
    hm.stop_monitoring()

def get_current_health() -> Dict[str, Any]:
    """Get current health status"""
    hm = get_health_monitor()
    return hm.get_current_health()

def get_health_report(include_history: bool = False) -> Dict[str, Any]:
    """Get health report"""
    hm = get_health_monitor()
    return hm.get_health_report(include_history)
