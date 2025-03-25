import os
import sys
import time
import json
import logging
import threading
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
import asyncio

logger = logging.getLogger(__name__)

class ModelingEngine:
    """Manages 3D modeling capabilities"""
    
    def __init__(self, data_dir=None, use_gpu=True):
        if data_dir is None:
            self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "modeling")
        else:
            self.data_dir = data_dir
            
        # Create directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Configuration
        self.use_gpu = use_gpu
        self.enabled = False
        self.loaded_engines = {}  # Which engines are loaded
        self.available_engines = {}  # Available engines and their capabilities
        
        # Output directory for generated models
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "models")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Background thread for heavy processing
        self.process_thread = None
        self.should_run = False
        self.process_queue = asyncio.Queue()
        
        # Project data
        self.current_project = None
        self.projects = {}
        self.model_history = []
        
        # Load configuration
        self.load_config()
        
        # Detect available engines
        self.detect_available_engines()
    
    def load_config(self) -> bool:
        """Load modeling configuration"""
        try:
            config_path = os.path.join(self.data_dir, "modeling_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.enabled = config.get("enabled", False)
                self.use_gpu = config.get("use_gpu", True)
                
                logger.info("Loaded 3D modeling configuration")
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading modeling configuration: {str(e)}")
            return False
    
    def save_config(self) -> bool:
        """Save modeling configuration"""
        try:
            config = {
                "enabled": self.enabled,
                "use_gpu": self.use_gpu
            }
            
            config_path = os.path.join(self.data_dir, "modeling_config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            logger.info("Saved 3D modeling configuration")
            return True
        except Exception as e:
            logger.error(f"Error saving modeling configuration: {str(e)}")
            return False
    
    def detect_available_engines(self) -> bool:
        """Detect available 3D modeling engines"""
        try:
            engines = {}
            
            # Try to import various 3D modeling libraries
            
            # 1. Try Blender Python API
            try:
                import bpy
                engines["blender"] = {
                    "available": True,
                    "version": bpy.app.version_string,
                    "capabilities": ["modeling", "sculpting", "rendering", "animation"],
                    "gpu_support": True
                }
            except ImportError:
                engines["blender"] = {
                    "available": False,
                    "error": "Blender Python API not found"
                }
            
            # 2. Try PyTorch3D
            try:
                import torch
                import pytorch3d
                engines["pytorch3d"] = {
                    "available": True,
                    "version": pytorch3d.__version__,
                    "capabilities": ["neural_rendering", "mesh_processing", "differentiable_rendering"],
                    "gpu_support": torch.cuda.is_available()
                }
            except ImportError:
                engines["pytorch3d"] = {
                    "available": False,
                    "error": "PyTorch3D not found"
                }
            
            # 3. Try Open3D
            try:
                import open3d as o3d
                engines["open3d"] = {
                    "available": True,
                    "version": o3d.__version__,
                    "capabilities": ["point_cloud", "mesh_processing", "reconstruction"],
                    "gpu_support": True  # Simplified, should check properly
                }
            except ImportError:
                engines["open3d"] = {
                    "available": False,
                    "error": "Open3D not found"
                }
            
            # 4. Try Trimesh for basic mesh processing
            try:
                import trimesh
                engines["trimesh"] = {
                    "available": True,
                    "version": trimesh.__version__,
                    "capabilities": ["mesh_processing", "import_export"],
                    "gpu_support": False
                }
            except ImportError:
                engines["trimesh"] = {
                    "available": False,
                    "error": "Trimesh not found"
                }
            
            # Update available engines
            self.available_engines = engines
            
            # Check if we have at least one working engine
            working_engines = [name for name, info in engines.items() if info.get("available", False)]
            
            if working_engines:
                logger.info(f"Detected {len(working_engines)} working 3D modeling engines: {', '.join(working_engines)}")
                return True
            else:
                logger.warning("No working 3D modeling engines detected")
                return False
                
        except Exception as e:
            logger.error(f"Error detecting 3D modeling engines: {str(e)}")
            return False
    
    def enable(self, state: bool = True) -> bool:
        """Enable or disable 3D modeling"""
        self.enabled = state
        
        if state and not self.is_running():
            self.start()
        elif not state and self.is_running():
            self.stop()
            
        self.save_config()
        return self.enabled
    
    def is_running(self) -> bool:
        """Check if the modeling engine is running"""
        return self.process_thread is not None and self.process_thread.is_alive()
    
    def start(self) -> bool:
        """Start the modeling engine"""
        if self.is_running():
            logger.warning("3D modeling engine is already running")
            return True
            
        try:
            self.should_run = True
            self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
            self.process_thread.start()
            logger.info("Started 3D modeling engine")
            return True
        except Exception as e:
            logger.error(f"Error starting 3D modeling engine: {str(e)}")
            return False
    
    def stop(self) -> bool:
        """Stop the modeling engine"""
        if not self.is_running():
            logger.warning("3D modeling engine is not running")
            return True
            
        try:
            self.should_run = False
            
            # Wait for thread to end
            if self.process_thread:
                self.process_thread.join(timeout=2.0)
                self.process_thread = None
                
            logger.info("Stopped 3D modeling engine")
            return True
        except Exception as e:
            logger.error(f"Error stopping 3D modeling engine: {str(e)}")
            return False
    
    def _process_loop(self):
        """Background thread for processing modeling tasks"""
        try:
            # Create an event loop for async tasks
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Start the processing loop
            loop.run_until_complete(self._async_process_loop())
            
        except Exception as e:
            logger.error(f"Error in 3D modeling process loop: {str(e)}")
    
    async def _async_process_loop(self):
        """Async loop for processing modeling tasks"""
        while self.should_run:
            try:
                # Get a task from the queue with timeout
                try:
                    task_data = await asyncio.wait_for(self.process_queue.get(), timeout=1.0)
                    
                    # Process the task
                    task_type = task_data.get("type", "")
                    
                    if task_type == "generate_from_text":
                        await self._process_text_to_model(task_data)
                    elif task_type == "convert_model":
                        await self._process_model_conversion(task_data)
                    elif task_type == "optimize_model":
                        await self._process_model_optimization(task_data)
                    else:
                        logger.warning(f"Unknown task type: {task_type}")
                        
                except asyncio.TimeoutError:
                    # No tasks in the queue, just continue
                    pass
                    
            except Exception as e:
                logger.error(f"Error processing modeling task: {str(e)}")
                await asyncio.sleep(1.0)  # Sleep on error to avoid tight loop
    
    async def _process_text_to_model(self, task_data: Dict[str, Any]):
        """Process text-to-3D-model generation task"""
        try:
            text_prompt = task_data.get("prompt", "")
            callback = task_data.get("callback")
            task_id = task_data.get("id", "")
            
            logger.info(f"Processing text-to-model task: {text_prompt[:50]}...")
            
            # Output path for the generated model
            timestamp = int(time.time())
            sanitized_name = ''.join(c if c.isalnum() else '_' for c in text_prompt[:30])
            output_file = os.path.join(self.output_dir, f"{sanitized_name}_{timestamp}.obj")
            
            # Check if we have a capable engine
            capable_engines = []
            
            # PyTorch3D for text-to-model (if text-to-3D capability is available)
            if (self.available_engines.get("pytorch3d", {}).get("available", False) and 
                "neural_rendering" in self.available_engines["pytorch3d"].get("capabilities", [])):
                capable_engines.append("pytorch3d")
            
            if not capable_engines:
                error_msg = "No capable engines for text-to-model generation"
                logger.error(error_msg)
                
                # Call callback with error if provided
                if callback:
                    callback({
                        "success": False,
                        "error": error_msg,
                        "id": task_id
                    })
                return
            
            # Select the best engine (for now just use the first one)
            engine_name = capable_engines[0]
            
            # Process based on engine
            if engine_name == "pytorch3d":
                # Placeholder for actual PyTorch3D implementation
                # In a real implementation, this would use a text-to-3D model
                
                # For demonstration purposes, we'll create a simple placeholder OBJ file
                with open(output_file, 'w') as f:
                    f.write("# Placeholder model generated from text\n")
                    f.write("# Text prompt: " + text_prompt + "\n")
                    f.write("v 0 0 0\n")
                    f.write("v 1 0 0\n")
                    f.write("v 0 1 0\n")
                    f.write("v 0 0 1\n")
                    f.write("f 1 2 3\n")
                    f.write("f 1 3 4\n")
                    f.write("f 1 4 2\n")
                    f.write("f 2 4 3\n")
            
            # Add to model history
            model_info = {
                "path": output_file,
                "name": os.path.basename(output_file),
                "type": "text-to-model",
                "prompt": text_prompt,
                "engine": engine_name,
                "timestamp": timestamp
            }
            
            self.model_history.append(model_info)
            
            # Call callback if provided
            if callback:
                callback({
                    "success": True,
                    "model_info": model_info,
                    "id": task_id
                })
                
        except Exception as e:
            error_msg = f"Error in text-to-model processing: {str(e)}"
            logger.error(error_msg)
            
            # Call callback with error if provided
            if callback:
                callback({
                    "success": False,
                    "error": error_msg,
                    "id": task_id
                })
    
    async def _process_model_conversion(self, task_data: Dict[str, Any]):
        """Process model format conversion task"""
        try:
            source_path = task_data.get("source_path", "")
            target_format = task_data.get("target_format", "obj")
            callback = task_data.get("callback")
            task_id = task_data.get("id", "")
            
            if not os.path.exists(source_path):
                error_msg = f"Source model not found: {source_path}"
                logger.error(error_msg)
                if callback:
                    callback({
                        "success": False,
                        "error": error_msg,
                        "id": task_id
                    })
                return
                
            logger.info(f"Converting model from {source_path} to {target_format}")
            
            # Determine source format
            source_format = os.path.splitext(source_path)[1][1:].lower()
            
            # Output path
            output_dir = os.path.dirname(source_path)
            filename = os.path.basename(source_path)
            name_without_ext = os.path.splitext(filename)[0]
            output_file = os.path.join(output_dir, f"{name_without_ext}.{target_format}")
            
            # Check for capable engines
            capable_engines = []
            
            if self.available_engines.get("trimesh", {}).get("available", False):
                capable_engines.append("trimesh")
                
            if self.available_engines.get("open3d", {}).get("available", False):
                capable_engines.append("open3d")
                
            if not capable_engines:
                error_msg = "No capable engines for model conversion"
                logger.error(error_msg)
                if callback:
                    callback({
                        "success": False,
                        "error": error_msg,
                        "id": task_id
                    })
                return
                
            # Select engine
            engine_name = capable_engines[0]
            
            # Perform conversion
            if engine_name == "trimesh":
                # Use trimesh for conversion
                import trimesh
                mesh = trimesh.load(source_path)
                mesh.export(output_file, file_type=target_format)
                
            elif engine_name == "open3d":
                # Use Open3D for conversion
                import open3d as o3d
                if source_format == "obj":
                    mesh = o3d.io.read_triangle_mesh(source_path)
                elif source_format == "ply":
                    mesh = o3d.io.read_point_cloud(source_path)
                else:
                    error_msg = f"Unsupported source format: {source_format}"
                    logger.error(error_msg)
                    if callback:
                        callback({
                            "success": False,
                            "error": error_msg,
                            "id": task_id
                        })
                    return
                    
                if target_format == "obj":
                    o3d.io.write_triangle_mesh(output_file, mesh)
                elif target_format == "ply":
                    o3d.io.write_point_cloud(output_file, mesh)
                else:
                    error_msg = f"Unsupported target format: {target_format}"
                    logger.error(error_msg)
                    if callback:
                        callback({
                            "success": False,
                            "error": error_msg,
                            "id": task_id
                        })
                    return
            
            # Add to model history
            model_info = {
                "path": output_file,
                "name": os.path.basename(output_file),
                "type": "converted",
                "source": source_path,
                "engine": engine_name,
                "timestamp": int(time.time())
            }
            
            self.model_history.append(model_info)
            
            # Call callback
            if callback:
                callback({
                    "success": True,
                    "model_info": model_info,
                    "id": task_id
                })
                
        except Exception as e:
            error_msg = f"Error in model conversion: {str(e)}"
            logger.error(error_msg)
            if callback:
                callback({
                    "success": False,
                    "error": error_msg,
                    "id": task_id
                })
    
    async def _process_model_optimization(self, task_data: Dict[str, Any]):
        """Process model optimization task"""
        try:
            source_path = task_data.get("source_path", "")
            optimization_type = task_data.get("optimization_type", "simplify")
            parameters = task_data.get("parameters", {})
            callback = task_data.get("callback")
            task_id = task_data.get("id", "")
            
            if not os.path.exists(source_path):
                error_msg = f"Source model not found: {source_path}"
                logger.error(error_msg)
                if callback:
                    callback({
                        "success": False,
                        "error": error_msg,
                        "id": task_id
                    })
                return
                
            logger.info(f"Optimizing model: {source_path}, type: {optimization_type}")
            
            # Output path
            output_dir = os.path.dirname(source_path)
            filename = os.path.basename(source_path)
            name_without_ext = os.path.splitext(filename)[0]
            ext = os.path.splitext(filename)[1]
            output_file = os.path.join(output_dir, f"{name_without_ext}_optimized{ext}")
            
            # Check for capable engines
            capable_engines = []
            
            if self.available_engines.get("trimesh", {}).get("available", False):
                capable_engines.append("trimesh")
                
            if self.available_engines.get("open3d", {}).get("available", False):
                capable_engines.append("open3d")
                
            if not capable_engines:
                error_msg = "No capable engines for model optimization"
                logger.error(error_msg)
                if callback:
                    callback({
                        "success": False,
                        "error": error_msg,
                        "id": task_id
                    })
                return
                
            # Select engine
            engine_name = capable_engines[0]
            
            # Perform optimization
            if engine_name == "trimesh":
                # Use trimesh for optimization
                import trimesh
                mesh = trimesh.load(source_path)
                
                if optimization_type == "simplify":
                    # Get desired face count
                    face_count = parameters.get("face_count", int(len(mesh.faces) * 0.5))  # Default: reduce by 50%
                    
                    # Simplify mesh
                    mesh = mesh.simplify_quadratic_decimation(face_count)
                    
                elif optimization_type == "repair":
                    # Fix broken topology
                    mesh.fill_holes()
                    mesh.remove_duplicate_faces()
                    mesh.remove_degenerate_faces()
                    mesh.fix_normals()
                    
                # Save optimized mesh
                mesh.export(output_file)
                
            elif engine_name == "open3d":
                # Use Open3D for optimization
                import open3d as o3d
                mesh = o3d.io.read_triangle_mesh(source_path)
                
                if optimization_type == "simplify":
                    # Get desired face count
                    original_triangles = len(mesh.triangles)
                    target_ratio = parameters.get("ratio", 0.5)  # Default: reduce by 50%
                    target_triangles = int(original_triangles * target_ratio)
                    
                    # Simplify mesh
                    mesh = mesh.simplify_quadric_decimation(target_triangles)
                    
                elif optimization_type == "repair":
                    # Fix broken topology
                    mesh.remove_duplicated_vertices()
                    mesh.remove_duplicated_triangles()
                    mesh.remove_degenerate_triangles()
                    mesh.compute_vertex_normals()
                    
                # Save optimized mesh
                o3d.io.write_triangle_mesh(output_file, mesh)
            
            # Add to model history
            model_info = {
                "path": output_file,
                "name": os.path.basename(output_file),
                "type": "optimized",
                "optimization_type": optimization_type,
                "source": source_path,
                "engine": engine_name,
                "timestamp": int(time.time())
            }
            
            self.model_history.append(model_info)
            
            # Call callback
            if callback:
                callback({
                    "success": True,
                    "model_info": model_info,
                    "id": task_id
                })
                
        except Exception as e:
            error_msg = f"Error in model optimization: {str(e)}"
            logger.error(error_msg)
            if callback:
                callback({
                    "success": False,
                    "error": error_msg,
                    "id": task_id
                })
    
    def generate_model_from_text(self, prompt: str, callback=None) -> str:
        """Queue text-to-3D-model generation
        
        Args:
            prompt: Text description of the 3D model to generate
            callback: Optional callback function for result
            
        Returns:
            str: Task ID
        """
        try:
            if not self.enabled:
                error_msg = "3D modeling is disabled"
                logger.warning(error_msg)
                if callback:
                    callback({"success": False, "error": error_msg})
                return ""
                
            # Create a task ID
            task_id = f"model_{int(time.time())}_{os.urandom(4).hex()}"
            
            # Create task data
            task_data = {
                "type": "generate_from_text",
                "prompt": prompt,
                "callback": callback,
                "id": task_id
            }
            
            # Add to queue (use asyncio.run for the thread-safe operation)
            if not self.is_running():
                self.start()
                
            # Use loop.call_soon_threadsafe to safely add to queue from another thread
            loop = asyncio.get_event_loop()
            future = asyncio.run_coroutine_threadsafe(self.process_queue.put(task_data), loop)
            future.result(timeout=1.0)  # Wait for the task to be added with timeout
            
            return task_id
            
        except Exception as e:
            error_msg = f"Error queuing text-to-model generation: {str(e)}"
            logger.error(error_msg)
            if callback:
                callback({"success": False, "error": error_msg})
            return ""
    
    def convert_model(self, source_path: str, target_format: str, callback=None) -> str:
        """Queue model format conversion
        
        Args:
            source_path: Path to the source model file
            target_format: Target format (obj, ply, stl, etc.)
            callback: Optional callback function for result
            
        Returns:
            str: Task ID
        """
        try:
            if not self.enabled:
                error_msg = "3D modeling is disabled"
                logger.warning(error_msg)
                if callback:
                    callback({"success": False, "error": error_msg})
                return ""
                
            # Create a task ID
            task_id = f"convert_{int(time.time())}_{os.urandom(4).hex()}"
            
            # Create task data
            task_data = {
                "type": "convert_model",
                "source_path": source_path,
                "target_format": target_format,
                "callback": callback,
                "id": task_id
            }
            
            # Add to queue
            if not self.is_running():
                self.start()
                
            loop = asyncio.get_event_loop()
            future = asyncio.run_coroutine_threadsafe(self.process_queue.put(task_data), loop)
            future.result(timeout=1.0)
            
            return task_id
            
        except Exception as e:
            error_msg = f"Error queuing model conversion: {str(e)}"
            logger.error(error_msg)
            if callback:
                callback({"success": False, "error": error_msg})
            return ""
    
    def optimize_model(self, source_path: str, optimization_type: str = "simplify", parameters: Dict[str, Any] = None, callback=None) -> str:
        """Queue model optimization
        
        Args:
            source_path: Path to the source model file
            optimization_type: Type of optimization (simplify, repair, etc.)
            parameters: Optimization parameters
            callback: Optional callback function for result
            
        Returns:
            str: Task ID
        """
        try:
            if not self.enabled:
                error_msg = "3D modeling is disabled"
                logger.warning(error_msg)
                if callback:
                    callback({"success": False, "error": error_msg})
                return ""
                
            # Create a task ID
            task_id = f"optimize_{int(time.time())}_{os.urandom(4).hex()}"
            
            # Create task data
            task_data = {
                "type": "optimize_model",
                "source_path": source_path,
                "optimization_type": optimization_type,
                "parameters": parameters or {},
                "callback": callback,
                "id": task_id
            }
            
            # Add to queue
            if not self.is_running():
                self.start()
                
            loop = asyncio.get_event_loop()
            future = asyncio.run_coroutine_threadsafe(self.process_queue.put(task_data), loop)
            future.result(timeout=1.0)
            
            return task_id
            
        except Exception as e:
            error_msg = f"Error queuing model optimization: {str(e)}"
            logger.error(error_msg)
            if callback:
                callback({"success": False, "error": error_msg})
            return ""
    
    def get_available_engines(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available 3D modeling engines"""
        return self.available_engines
    
    def get_model_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get history of generated models
        
        Args:
            limit: Maximum number of models to return
            
        Returns:
            List[Dict[str, Any]]: List of model information
        """
        # Sort by timestamp (newest first) and apply limit
        sorted_history = sorted(
            self.model_history, 
            key=lambda x: x.get("timestamp", 0), 
            reverse=True
        )
        
        return sorted_history[:limit]
    
    def load_model(self, model_path: str) -> Dict[str, Any]:
        """Load a 3D model and return information about it
        
        Args:
            model_path: Path to the model file
            
        Returns:
            Dict[str, Any]: Model information
        """
        try:
            if not os.path.exists(model_path):
                return {"error": f"Model not found: {model_path}"}
                
            # Determine file format
            file_ext = os.path.splitext(model_path)[1][1:].lower()
            
            # Check if we have a capable engine
            capable_engines = []
            
            if self.available_engines.get("trimesh", {}).get("available", False):
                capable_engines.append("trimesh")
                
            if self.available_engines.get("open3d", {}).get("available", False):
                capable_engines.append("open3d")
                
            if not capable_engines:
                return {"error": "No capable engines for loading this model"}
                
            # Select engine
            engine_name = capable_engines[0]
            
            # Load and analyze model
            if engine_name == "trimesh":
                import trimesh
                mesh = trimesh.load(model_path)
                
                # Calculate metrics
                model_info = {
                    "path": model_path,
                    "name": os.path.basename(model_path),
                    "format": file_ext,
                    "vertices": len(mesh.vertices),
                    "faces": len(mesh.faces),
                    "bounding_box": mesh.bounds.tolist(),
                    "center_mass": mesh.center_mass.tolist(),
                    "volume": float(mesh.volume) if mesh.is_watertight else None,
                    "is_watertight": mesh.is_watertight,
                    "engine": engine_name
                }
                
            elif engine_name == "open3d":
                import open3d as o3d
                
                if file_ext in ["obj", "ply", "stl"]:
                    mesh = o3d.io.read_triangle_mesh(model_path)
                    
                    # Calculate metrics
                    model_info = {
                        "path": model_path,
                        "name": os.path.basename(model_path),
                        "format": file_ext,
                        "vertices": len(mesh.vertices),
                        "faces": len(mesh.triangles),
                        "bounding_box": [mesh.get_min_bound().tolist(), mesh.get_max_bound().tolist()],
                        "center": mesh.get_center().tolist(),
                        "volume": float(mesh.get_volume()) if mesh.is_watertight() else None,
                        "is_watertight": mesh.is_watertight(),
                        "engine": engine_name
                    }
                else:
                    return {"error": f"Unsupported file format: {file_ext}"}
            
            return model_info
            
        except Exception as e:
            error_msg = f"Error loading model: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

# Global instance
_modeling_engine = None

def get_modeling_engine():
    """Get the global modeling engine instance"""
    global _modeling_engine
    if _modeling_engine is None:
        _modeling_engine = ModelingEngine()
    return _modeling_engine
