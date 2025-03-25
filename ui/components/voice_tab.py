"""
Voice tab UI component
"""
import gradio as gr
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .base import TabComponent

class VoiceTab(TabComponent):
    """Voice tab UI component"""
    
    def build(self):
        """Build the voice processing tab"""
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### Text to Speech")
                
                tts_text = gr.Textbox(
                    placeholder="Enter text to convert to speech...",
                    label="Text",
                    lines=5
                )
                
                with gr.Row():
                    voice = gr.Dropdown(
                        choices=list(self.bot.voice_handler.voices.keys()),
                        value=self.bot.voice_handler.active_voice,
                        label="Voice"
                    )
                    
                    tts_btn = gr.Button("Convert to Speech", variant="primary")
                
                tts_output = gr.Audio(label="Generated Speech", type="filepath")
                tts_status = gr.Markdown("")
            
            with gr.Column(scale=2):
                gr.Markdown("### Speech to Text")
                
                audio_input = gr.Audio(label="Upload or Record Audio", type="filepath")
                stt_btn = gr.Button("Transcribe Audio")
                stt_output = gr.Textbox(label="Transcription", lines=5)
                stt_status = gr.Markdown("")
        
        # Voice modulation section (this was missing/incomplete before)
        with gr.Row():
            gr.Markdown("### Voice Modulation")
            
            with gr.Column():
                mod_audio_input = gr.Audio(label="Upload Audio to Modulate", type="filepath")
                
                with gr.Row():
                    pitch = gr.Slider(0.5, 2.0, value=1.0, label="Pitch", 
                                     info="Adjust voice pitch (0.5=lower, 1.0=normal, 2.0=higher)")
                    speed = gr.Slider(0.5, 2.0, value=1.0, label="Speed",
                                     info="Adjust playback speed (0.5=slower, 1.0=normal, 2.0=faster)")
                
                mod_btn = gr.Button("Modulate Voice", variant="primary")
                
                mod_output = gr.Audio(label="Modulated Voice Output", type="filepath")
                mod_status = gr.Markdown("")
        
        # Store elements for later access
        self.elements.update({
            "tts_text": tts_text,
            "voice": voice,
            "tts_btn": tts_btn,
            "tts_output": tts_output,
            "tts_status": tts_status,
            "audio_input": audio_input,
            "stt_btn": stt_btn,
            "stt_output": stt_output,
            "stt_status": stt_status,
            "mod_audio_input": mod_audio_input,
            "pitch": pitch,
            "speed": speed,
            "mod_btn": mod_btn,
            "mod_output": mod_output,
            "mod_status": mod_status
        })
        
        # Set up event handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up event handlers for this tab"""
        e = self.elements
        
        # TTS button handler
        e["tts_btn"].click(
            fn=self._on_text_to_speech,
            inputs=[e["tts_text"], e["voice"]],
            outputs=[e["tts_output"], e["tts_status"]]
        )
        
        # STT button handler
        e["stt_btn"].click(
            fn=self._on_speech_to_text,
            inputs=[e["audio_input"]],
            outputs=[e["stt_output"], e["stt_status"]]
        )
        
        # Voice modulation button handler
        e["mod_btn"].click(
            fn=self._on_voice_modulate,
            inputs=[e["mod_audio_input"], e["pitch"], e["speed"]],
            outputs=[e["mod_output"], e["mod_status"]]
        )
    
    def _on_text_to_speech(self, text, voice):
        """Handle text to speech conversion"""
        if not text:
            return None, "Please enter text to convert to speech."
        
        audio_path = self.bot.text_to_speech(text, voice)
        
        if not audio_path:
            return None, "Failed to convert text to speech. Please try again."
        
        return audio_path, "Text successfully converted to speech."
    
    def _on_speech_to_text(self, audio_path):
        """Handle speech to text conversion"""
        if not audio_path:
            return "Please upload or record audio to transcribe.", ""
        
        transcription = self.bot.voice_handler.speech_to_text(audio_path)
        return transcription, "Audio successfully transcribed."
    
    def _on_voice_modulate(self, audio_path, pitch, speed):
        """Handle voice modulation"""
        if not audio_path:
            return None, "Please upload audio to modulate."
        
        modulated_path = self.bot.voice_handler.modulate_voice(audio_path, pitch, speed)
        
        if not modulated_path:
            return None, "Failed to modulate voice. Please try again."
        
        return modulated_path, f"Voice successfully modulated with pitch={pitch}, speed={speed}."
