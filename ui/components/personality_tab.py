"""
Personality tab UI component
"""
import gradio as gr
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .base import TabComponent

class PersonalityTab(TabComponent):
    """Personality tab UI component"""
    
    def build(self):
        """Build the personality settings tab"""
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### Personality Settings")
                gr.Markdown("Adjust how Lyra responds and communicates")
                
                # Basic personality traits
                with gr.Group():
                    gr.Markdown("#### Basic Traits")
                    creativity = gr.Slider(0.0, 1.0, value=self.bot.personality.settings["creativity"], 
                                         label="Creativity", 
                                         info="Low: Factual, High: Creative")
                    
                    formality = gr.Slider(0.0, 1.0, value=self.bot.personality.settings["formality"], 
                                        label="Formality", 
                                        info="Low: Casual, High: Formal")
                    
                    verbosity = gr.Slider(0.0, 1.0, value=self.bot.personality.settings["verbosity"], 
                                        label="Verbosity", 
                                        info="Low: Concise, High: Detailed")
                    
                    empathy = gr.Slider(0.0, 1.0, value=self.bot.personality.settings["empathy"], 
                                      label="Empathy", 
                                      info="Low: Analytical, High: Empathetic")
                    
                    humor = gr.Slider(0.0, 1.0, value=self.bot.personality.settings["humor"], 
                                    label="Humor", 
                                    info="Low: Serious, High: Humorous")
                    
                    assertiveness = gr.Slider(0.0, 1.0, value=self.bot.personality.settings["assertiveness"], 
                                            label="Assertiveness", 
                                            info="Low: Passive, High: Confident")
                    
                    logic = gr.Slider(0.0, 1.0, value=self.bot.personality.settings["logic"], 
                                    label="Logic", 
                                    info="Low: Intuitive, High: Logical")
                
                with gr.Row():
                    creativity_style = gr.Dropdown(
                        choices=["balanced", "narrative", "poetic", "technical"],
                        value=self.bot.personality.settings["creativity_style"],
                        label="Creativity Style"
                    )
                    
                    nsfw_tolerance = gr.Slider(0.0, 1.0, value=self.bot.personality.settings.get("nsfw_tolerance", 0.5), 
                                             label="Adult Content Tolerance", 
                                             info="Low: Conservative, High: Open")
                
                # Special modes
                with gr.Group():
                    gr.Markdown("#### Special Personality Modes")
                    with gr.Row():
                        uwu_mode = gr.Slider(0.0, 1.0, value=self.bot.personality.settings.get("uwu_mode", 0.0), 
                                           label="UwU Mode", 
                                           info="Cutesy, affectionate anime-style")
                        
                        dark_mode = gr.Slider(0.0, 1.0, value=self.bot.personality.settings.get("dark_mode", 0.0), 
                                            label="Dark Mode", 
                                            info="Brooding, nihilistic, emo style")
                    
                    with gr.Row():
                        aggressive = gr.Slider(0.0, 1.0, value=self.bot.personality.settings.get("aggressive", 0.0), 
                                              label="Aggressive", 
                                              info="Short-tempered, strong language")
                        
                        drunk = gr.Slider(0.0, 1.0, value=self.bot.personality.settings.get("drunk", 0.0), 
                                         label="Drunk Mode", 
                                         info="Slurred speech, lowered inhibitions")
                    
                    sarcasm = gr.Slider(0.0, 1.0, value=self.bot.personality.settings.get("sarcasm", 0.0), 
                                     label="Sarcasm", 
                                     info="Witty, ironic remarks")
                
                # Accent modes
                with gr.Group():
                    gr.Markdown("#### Accent/Dialect")
                    with gr.Row():
                        scottish = gr.Slider(0.0, 1.0, value=self.bot.personality.settings.get("scottish", 0.0), 
                                           label="Scottish", 
                                           info="Scottish accent and expressions")
                        
                        british = gr.Slider(0.0, 1.0, value=self.bot.personality.settings.get("british", 0.0), 
                                          label="British", 
                                          info="British accent and expressions")
                    
                    with gr.Row():
                        german = gr.Slider(0.0, 1.0, value=self.bot.personality.settings.get("german", 0.0), 
                                         label="German", 
                                         info="German accent and expressions")
                        
                        australian = gr.Slider(0.0, 1.0, value=self.bot.personality.settings.get("australian", 0.0), 
                                             label="Australian", 
                                             info="Australian accent and expressions")
                
                save_btn = gr.Button("Save Personality Settings", variant="primary")
                settings_status = gr.Markdown("")
            
            with gr.Column(scale=1):
                gr.Markdown("### Presets")
                gr.Markdown("Save and load personality configurations")
                
                # Preset dropdown
                presets_dropdown = gr.Dropdown(
                    choices=self.bot.personality.get_preset_names(),
                    label="Personality Presets",
                    value=self.bot.personality.get_active_preset()
                )
                
                preset_description = gr.Markdown("")
                
                load_preset_btn = gr.Button("Load Selected Preset")
                delete_preset_btn = gr.Button("Delete Selected Preset", variant="stop")
                
                gr.Markdown("### Save New Preset")
                preset_name = gr.Textbox(placeholder="Name for new preset", label="Preset Name")
                preset_desc = gr.Textbox(placeholder="Description (optional)", label="Description", lines=2)
                save_preset_btn = gr.Button("Save Current Settings as Preset")
                
                preset_status = gr.Markdown("")
                
                gr.Markdown("### Test Personality")
                test_prompt = gr.Textbox(
                    placeholder="Enter a test prompt to see how Lyra responds with current settings...",
                    label="Test Prompt",
                    lines=2,
                    value="Tell me what you think about modern technology."
                )
                test_btn = gr.Button("Test Personality")
                test_result = gr.Textbox(label="Result", lines=5)
        
        # Store elements for later access
        self.elements.update({
            "creativity": creativity,
            "formality": formality,
            "verbosity": verbosity,
            "empathy": empathy,
            "humor": humor,
            "assertiveness": assertiveness,
            "logic": logic,
            "creativity_style": creativity_style,
            "nsfw_tolerance": nsfw_tolerance,
            "uwu_mode": uwu_mode,
            "dark_mode": dark_mode,
            "aggressive": aggressive,
            "drunk": drunk,
            "sarcasm": sarcasm,
            "scottish": scottish,
            "british": british,
            "german": german,
            "australian": australian,
            "save_btn": save_btn,
            "settings_status": settings_status,
            "presets_dropdown": presets_dropdown,
            "preset_description": preset_description,
            "load_preset_btn": load_preset_btn,
            "delete_preset_btn": delete_preset_btn,
            "preset_name": preset_name,
            "preset_desc": preset_desc,
            "save_preset_btn": save_preset_btn,
            "preset_status": preset_status,
            "test_prompt": test_prompt,
            "test_btn": test_btn,
            "test_result": test_result
        })
        
        # Set up event handlers
        self._setup_handlers()
        
        # Update preset description
        self._update_preset_description(self.bot.personality.get_active_preset())
    
    def _setup_handlers(self):
        """Set up event handlers for this tab"""
        e = self.elements
        
        # Save settings button handler
        e["save_btn"].click(
            fn=self._on_save_personality_settings,
            inputs=[
                e["creativity"], e["formality"], e["verbosity"], e["empathy"],
                e["humor"], e["assertiveness"], e["logic"], e["creativity_style"],
                e["uwu_mode"], e["dark_mode"], e["aggressive"], e["drunk"],
                e["scottish"], e["british"], e["german"], e["australian"],
                e["nsfw_tolerance"], e["sarcasm"]
            ],
            outputs=[e["settings_status"]]
        )
        
        # Preset selection change handler
        e["presets_dropdown"].change(
            fn=self._update_preset_description,
            inputs=[e["presets_dropdown"]],
            outputs=[e["preset_description"]]
        )
        
        # Load preset button handler
        e["load_preset_btn"].click(
            fn=self._on_load_preset,
            inputs=[e["presets_dropdown"]],
            outputs=[
                e["creativity"], e["formality"], e["verbosity"], e["empathy"],
                e["humor"], e["assertiveness"], e["logic"], e["creativity_style"],
                e["uwu_mode"], e["dark_mode"], e["aggressive"], e["drunk"],
                e["scottish"], e["british"], e["german"], e["australian"],
                e["nsfw_tolerance"], e["sarcasm"], e["preset_status"]
            ]
        )
        
        # Delete preset button handler
        e["delete_preset_btn"].click(
            fn=self._on_delete_preset,
            inputs=[e["presets_dropdown"]],
            outputs=[e["presets_dropdown"], e["preset_description"], e["preset_status"]]
        )
        
        # Save preset button handler
        e["save_preset_btn"].click(
            fn=self._on_save_preset,
            inputs=[e["preset_name"], e["preset_desc"]],
            outputs=[e["presets_dropdown"], e["preset_name"], e["preset_desc"], e["preset_status"]]
        )
        
        # Test personality button handler
        e["test_btn"].click(
            fn=self._on_test_personality,
            inputs=[e["test_prompt"]],
            outputs=[e["test_result"]]
        )
    
    def _on_save_personality_settings(self, creativity, formality, verbosity, empathy, 
                                     humor, assertiveness, logic, creativity_style,
                                     uwu_mode, dark_mode, aggressive, drunk, 
                                     scottish, british, german, australian,
                                     nsfw_tolerance, sarcasm):
        """Save personality settings"""
        settings = {
            "creativity": creativity,
            "formality": formality,
            "verbosity": verbosity,
            "empathy": empathy,
            "humor": humor,
            "assertiveness": assertiveness,
            "logic": logic,
            "creativity_style": creativity_style,
            "uwu_mode": uwu_mode,
            "dark_mode": dark_mode,
            "aggressive": aggressive,
            "drunk": drunk,
            "scottish": scottish,
            "british": british,
            "german": german,
            "australian": australian,
            "nsfw_tolerance": nsfw_tolerance,
            "sarcasm": sarcasm
        }
        
        self.bot.update_personality(**settings)
        return "Personality settings saved successfully."
    
    def _update_preset_description(self, preset_name):
        """Update the description for the selected preset"""
        description = self.bot.get_personality_preset_description(preset_name)
        return f"**{preset_name}**: {description}" if description else ""
    
    def _on_load_preset(self, preset_name):
        """Load a personality preset"""
        if not preset_name:
            return [0] * 17 + ["Please select a preset to load."]
        
        success = self.bot.load_personality_preset(preset_name)
        
        if success:
            # Get updated settings after loading
            settings = self.bot.personality.settings
            
            # Return all slider values in the correct order
            return [
                settings.get("creativity", 0.7),
                settings.get("formality", 0.5),
                settings.get("verbosity", 0.6),
                settings.get("empathy", 0.8),
                settings.get("humor", 0.6),
                settings.get("assertiveness", 0.5),
                settings.get("logic", 0.7),
                settings.get("creativity_style", "balanced"),
                settings.get("uwu_mode", 0),
                settings.get("dark_mode", 0),
                settings.get("aggressive", 0),
                settings.get("drunk", 0),
                settings.get("scottish", 0),
                settings.get("british", 0),
                settings.get("german", 0),
                settings.get("australian", 0),
                settings.get("nsfw_tolerance", 0.5),
                settings.get("sarcasm", 0),
                f"Preset '{preset_name}' loaded successfully."
            ]
        else:
            # Return current values plus error message
            settings = self.bot.personality.settings
            return [
                settings.get("creativity", 0.7),
                settings.get("formality", 0.5),
                settings.get("verbosity", 0.6),
                settings.get("empathy", 0.8),
                settings.get("humor", 0.6),
                settings.get("assertiveness", 0.5),
                settings.get("logic", 0.7),
                settings.get("creativity_style", "balanced"),
                settings.get("uwu_mode", 0),
                settings.get("dark_mode", 0),
                settings.get("aggressive", 0),
                settings.get("drunk", 0),
                settings.get("scottish", 0),
                settings.get("british", 0),
                settings.get("german", 0),
                settings.get("australian", 0),
                settings.get("nsfw_tolerance", 0.5),
                settings.get("sarcasm", 0),
                f"Failed to load preset '{preset_name}'."
            ]
    
    def _on_delete_preset(self, preset_name):
        """Delete a personality preset"""
        if not preset_name or preset_name == "default":
            return self.bot.get_personality_presets(), "", "Cannot delete default preset."
        
        success = self.bot.delete_personality_preset(preset_name)
        
        if success:
            return self.bot.get_personality_presets(), "", f"Preset '{preset_name}' deleted successfully."
        else:
            return self.bot.get_personality_presets(), self._update_preset_description(preset_name), f"Failed to delete preset '{preset_name}'."
    
    def _on_save_preset(self, preset_name, description):
        """Save current settings as a preset"""
        if not preset_name:
            return self.bot.get_personality_presets(), preset_name, description, "Please provide a name for the preset."
        
        success = self.bot.save_personality_preset(preset_name, description)
        
        if success:
            return self.bot.get_personality_presets(), "", "", f"Preset '{preset_name}' saved successfully."
        else:
            return self.bot.get_personality_presets(), preset_name, description, f"Failed to save preset '{preset_name}'."
    
    def _on_test_personality(self, prompt):
        """Test current personality settings with a sample prompt"""
        if not prompt:
            return "Please enter a test prompt."
        
        # Save current settings first
        settings = {
            "creativity": self.elements["creativity"].value,
            "formality": self.elements["formality"].value,
            "verbosity": self.elements["verbosity"].value,
            "empathy": self.elements["empathy"].value,
            "humor": self.elements["humor"].value,
            "assertiveness": self.elements["assertiveness"].value,
            "logic": self.elements["logic"].value,
            "creativity_style": self.elements["creativity_style"].value,
            "uwu_mode": self.elements["uwu_mode"].value,
            "dark_mode": self.elements["dark_mode"].value,
            "aggressive": self.elements["aggressive"].value,
            "drunk": self.elements["drunk"].value,
            "scottish": self.elements["scottish"].value,
            "british": self.elements["british"].value,
            "german": self.elements["german"].value,
            "australian": self.elements["australian"].value,
            "nsfw_tolerance": self.elements["nsfw_tolerance"].value,
            "sarcasm": self.elements["sarcasm"].value
        }
        
        self.bot.update_personality(**settings)
        
        # Generate a response with current settings
        response = self.bot.chat(
            message=prompt,
            include_profile=False,
            include_system_instructions=False,
            include_extras=False
        )
        
        return response
