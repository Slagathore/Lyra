"""
Code tab UI component
"""
import gradio as gr
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .base import TabComponent

class CodeTab(TabComponent):
    """Code tab UI component"""
    
    def build(self):
        """Build the code sandbox tab"""
        with gr.Row():
            with gr.Column(scale=3):
                description = gr.Textbox(
                    placeholder="Describe what the code should do...",
                    label="Code Description",
                    lines=3
                )
                
                with gr.Row():
                    language = gr.Dropdown(
                        choices=self.bot.code_sandbox.languages,
                        value="python",
                        label="Programming Language"
                    )
                    
                    generate_btn = gr.Button("Generate Code", variant="primary")
                
                code_output = gr.Code(label="Generated Code", language="python", lines=15)
                
                with gr.Row():
                    execute_btn = gr.Button("Execute Code")
                    save_btn = gr.Button("Save Code")
                
                execution_output = gr.Textbox(label="Execution Result", lines=5)
                status = gr.Markdown("")
            
            with gr.Column(scale=1):
                gr.Markdown("### Saved Code")
                code_name = gr.Textbox(placeholder="Name for saved code", label="Code Name")
                saved_codes = gr.Dropdown(label="Saved Code Files")
                refresh_btn = gr.Button("Refresh List")
                
                load_btn = gr.Button("Load Selected Code")
        
        # Store elements for later access
        self.elements.update({
            "description": description,
            "language": language,
            "generate_btn": generate_btn,
            "code_output": code_output,
            "execute_btn": execute_btn,
            "save_btn": save_btn,
            "execution_output": execution_output,
            "status": status,
            "code_name": code_name,
            "saved_codes": saved_codes,
            "refresh_btn": refresh_btn,
            "load_btn": load_btn
        })
        
        # Set up event handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up event handlers for this tab"""
        e = self.elements
        
        # Update language selection for code display
        e["language"].change(
            fn=lambda lang: gr.Code.update(language=lang),
            inputs=[e["language"]],
            outputs=[e["code_output"]]
        )
        
        # Code generation button handler
        e["generate_btn"].click(
            fn=self._on_code_generate,
            inputs=[e["description"], e["language"]],
            outputs=[e["code_output"], e["status"]]
        )
        
        # Code execution button handler
        e["execute_btn"].click(
            fn=self._on_code_execute,
            inputs=[e["code_output"], e["language"]],
            outputs=[e["execution_output"], e["status"]]
        )
        
        # Save code button handler
        e["save_btn"].click(
            fn=self._on_code_save,
            inputs=[e["code_output"], e["code_name"], e["language"]],
            outputs=[e["status"], e["code_name"], e["saved_codes"]]
        )
        
        # Refresh list button handler
        e["refresh_btn"].click(
            fn=self._on_refresh_code_list,
            outputs=[e["saved_codes"]]
        )
        
        # Load code button handler
        e["load_btn"].click(
            fn=self._on_load_code,
            inputs=[e["saved_codes"]],
            outputs=[e["code_output"], e["status"]]
        )
    
    def _on_code_generate(self, description, language):
        """Handle code generation"""
        if not description:
            return "", "Please provide a description of what the code should do."
        
        code = self.bot.generate_code(description, language)
        return code, f"Code generated successfully in {language}."
    
    def _on_code_execute(self, code, language):
        """Handle code execution"""
        if not code:
            return "No code to execute.", "Please generate or enter code first."
        
        result = self.bot.execute_code(code, language)
        
        if result["success"]:
            return result["output"], f"Code executed successfully in {result['execution_time']:.2f}s."
        else:
            return result.get("output", "Unknown error"), "Code execution failed."
    
    def _on_code_save(self, code, name, language):
        """Handle saving code to file"""
        if not code:
            return "No code to save.", name, None
        
        if not name:
            name = f"code_{int(time.time())}"
        
        file_path = self.bot.code_sandbox.save_code(code, name, language)
        
        if file_path:
            return f"Code saved to {file_path}", "", self._get_saved_code_files()
        else:
            return "Failed to save code.", name, None
    
    def _get_saved_code_files(self):
        """Get list of saved code files"""
        code_dir = self.bot.code_sandbox.output_dir
        if not code_dir.exists():
            return []
        
        code_files = list(code_dir.glob("*.*"))
        return [file.name for file in code_files]
    
    def _on_refresh_code_list(self):
        """Refresh the list of saved code files"""
        return self._get_saved_code_files()
    
    def _on_load_code(self, file_name):
        """Load code from a saved file"""
        if not file_name:
            return None, "Please select a file to load."
            
        try:
            code_dir = self.bot.code_sandbox.output_dir
            file_path = code_dir / file_name
            
            if not file_path.exists():
                return None, f"File {file_name} not found."
                
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
                
            return code, f"Loaded code from {file_name}"
        except Exception as e:
            return None, f"Error loading code: {str(e)}"
