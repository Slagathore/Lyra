"""
Smart Home tab UI component
"""
import gradio as gr
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .base import TabComponent

class SmartHomeTab(TabComponent):
    """Smart Home tab UI component"""
    
    def build(self):
        """Build the smart home control tab"""
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### Device Control")
                
                device_list = gr.Dropdown(
                    choices=list(self.bot.smart_home.get_devices().keys()),
                    label="Select Device"
                )
                
                device_info = gr.JSON(label="Device Information")
                
                with gr.Row():
                    command = gr.Dropdown(label="Command")
                    params = gr.Textbox(
                        placeholder="Parameters (JSON format, e.g. {\"temperature\": 72})",
                        label="Parameters (if needed)"
                    )
                
                control_btn = gr.Button("Send Command", variant="primary")
                
                result = gr.JSON(label="Command Result")
            
            with gr.Column(scale=1):
                gr.Markdown("### Add New Device")
                
                new_device_id = gr.Textbox(placeholder="Device ID", label="Device ID")
                new_device_name = gr.Textbox(placeholder="Device Name", label="Device Name")
                new_device_type = gr.Dropdown(
                    choices=["light", "climate", "switch", "sensor", "media"],
                    label="Device Type"
                )
                new_device_commands = gr.Textbox(
                    placeholder="Commands (comma separated)",
                    label="Supported Commands"
                )
                
                add_device_btn = gr.Button("Add Device")
                
                add_status = gr.Markdown("")
        
        # Store elements for later access
        self.elements.update({
            "device_list": device_list,
            "device_info": device_info,
            "command": command,
            "params": params,
            "control_btn": control_btn,
            "result": result,
            "new_device_id": new_device_id,
            "new_device_name": new_device_name,
            "new_device_type": new_device_type,
            "new_device_commands": new_device_commands,
            "add_device_btn": add_device_btn,
            "add_status": add_status
        })
        
        # Set up event handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up event handlers for this tab"""
        e = self.elements
        
        # Update device info and commands when device is selected
        e["device_list"].change(
            fn=self._on_device_select,
            inputs=[e["device_list"]],
            outputs=[e["device_info"], e["command"]]
        )
        
        # Control button handler
        e["control_btn"].click(
            fn=self._on_device_control,
            inputs=[e["device_list"], e["command"], e["params"]],
            outputs=[e["result"]]
        )
        
        # Add device button handler
        e["add_device_btn"].click(
            fn=self._on_add_device,
            inputs=[e["new_device_id"], e["new_device_name"], e["new_device_type"], e["new_device_commands"]],
            outputs=[e["add_status"], e["device_list"], e["new_device_id"], e["new_device_name"], e["new_device_commands"]]
        )
    
    def _on_device_select(self, device_id):
        """Handle device selection"""
        if not device_id:
            return {}, []
        
        devices = self.bot.smart_home.get_devices()
        if device_id not in devices:
            return {}, []
        
        device = devices[device_id]
        
        # Return device info and commands
        return device, device["commands"]
    
    def _on_device_control(self, device_id, command, params_str):
        """Handle device control"""
        if not device_id or not command:
            return {"success": False, "error": "Device ID and command are required."}
        
        # Parse parameters
        params = None
        if params_str:
            try:
                params = json.loads(params_str)
            except json.JSONDecodeError:
                return {"success": False, "error": "Invalid parameters format. Use valid JSON."}
        
        # Send command to device
        result = self.bot.control_smart_home(device_id, command, params)
        return result
    
    def _on_add_device(self, device_id, name, device_type, commands_str):
        """Handle adding a new device"""
        if not device_id or not name or not device_type:
            return "Please fill in device ID, name, and type.", None, device_id, name, commands_str
        
        # Parse commands
        commands = [cmd.strip() for cmd in commands_str.split(',') if cmd.strip()]
        if not commands:
            return "Please specify at least one command.", None, device_id, name, commands_str
        
        # Create device info
        device_info = {
            "name": name,
            "type": device_type,
            "status": "unknown",
            "commands": commands
        }
        
        # Add device
        success = self.bot.smart_home.add_device(device_id, device_info)
        
        if success:
            # Update device list
            return f"Device '{name}' added successfully.", list(self.bot.smart_home.get_devices().keys()), "", "", ""
        else:
            return f"Failed to add device. Device ID '{device_id}' may already exist.", None, device_id, name, commands_str
