# ...existing code...

def generate_speech(text, voice="en-US-Neural2-F", rate=1.0):
    try:
        logger.info(f"Generating speech from text: {text[:50]}...")
        
        # First try to use pyttsx3 (offline TTS)
        try:
            import pyttsx3
            import tempfile
            import os
            import time
            
            engine = pyttsx3.init()
            
            # Set properties
            engine.setProperty('rate', int(150 * rate))  # Speed of speech
            
            # Get available voices
            voices = engine.getProperty('voices')
            
            # Try to find a matching voice by name or language
            found_voice = None
            for v in voices:
                if voice.lower() in v.name.lower() or voice.lower() in v.languages[0].lower():
                    found_voice = v
                    break
            
            # Set voice if found, otherwise use default
            if found_voice:
                engine.setProperty('voice', found_voice.id)
            
            # Create a temporary file for the speech
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time())
            audio_file = os.path.join(temp_dir, f"lyra_speech_{timestamp}.mp3")
            
            # Generate and save the speech
            engine.save_to_file(text, audio_file)
            engine.runAndWait()
            
            logger.info(f"Speech generated successfully using pyttsx3 and saved to {audio_file}")
            return audio_file, None
            
        except Exception as e:
            logger.warning(f"Failed to use pyttsx3 for TTS: {str(e)}. Trying alternative method...")
            
            # Fallback to gTTS (requires internet)
            try:
                from gtts import gTTS
                import tempfile
                import os
                import time
                
                # Create a temporary file for the speech
                temp_dir = tempfile.gettempdir()
                timestamp = int(time.time())
                audio_file = os.path.join(temp_dir, f"lyra_speech_{timestamp}.mp3")
                
                # Determine language from voice parameter
                lang = 'en'
                if '-' in voice:
                    lang = voice.split('-')[0].lower()
                
                # Generate and save the speech
                tts = gTTS(text=text, lang=lang, slow=False)
                tts.save(audio_file)
                
                logger.info(f"Speech generated successfully using gTTS and saved to {audio_file}")
                return audio_file, None
                
            except Exception as e_gtts:
                error_msg = f"Failed to generate speech with gTTS: {str(e_gtts)}"
                logger.error(error_msg)
                return None, error_msg
    
    except Exception as e:
        error_msg = f"Error in generate_speech: {str(e)}"
        logger.error(error_msg)
        return None, error_msg

# ...existing code...
