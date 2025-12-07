import os
import time
from config.config import Config

# Try to import ElevenLabs, fallback to gTTS
try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings
    ELEVENLABS_AVAILABLE = True
    ELEVENLABS_V2 = True
except ImportError:
    try:
        # Try older API format (v1.x)
        from elevenlabs import generate, set_api_key, VoiceSettings, save
        ELEVENLABS_AVAILABLE = True
        ELEVENLABS_V2 = False
    except ImportError:
        ELEVENLABS_AVAILABLE = False
        ELEVENLABS_V2 = False

# Always import gTTS as fallback
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    gTTS = None

class TTSHandler:
    """Handle text-to-speech generation using ElevenLabs (with gTTS fallback)"""

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean text for TTS"""
        clean_text = text.replace("⚠️", "Warning:").replace("🟡", "").replace("🟢", "")
        clean_text = clean_text.replace("**", "").replace("*", "")
        clean_text = clean_text.replace("#", "")
        return clean_text

    @staticmethod
    def generate_audio(
        text: str,
        output_filename: str,
        language: str = 'en',
        slow: bool = False
    ) -> str:
        """
        Generate audio file from text using ElevenLabs (or gTTS fallback)
        Returns: path to audio file
        """
        # Ensure output directory exists
        os.makedirs(Config.AUDIO_DIR, exist_ok=True)

        # Clean text for TTS
        clean_text = TTSHandler._clean_text(text)

        # Generate audio
        output_path = os.path.join(Config.AUDIO_DIR, output_filename)

        # Use ElevenLabs if available and API key is set
        if ELEVENLABS_AVAILABLE and Config.ELEVENLABS_API_KEY:
            try:
                print("🎙️ Using ElevenLabs for TTS generation...")
                
                if ELEVENLABS_V2:
                    # New API (v2.x) - use text_to_speech.convert
                    client = ElevenLabs(api_key=Config.ELEVENLABS_API_KEY)
                    audio_generator = client.text_to_speech.convert(
                        voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel voice ID
                        text=clean_text,
                        model_id="eleven_multilingual_v2"
                    )
                    # Save audio stream
                    with open(output_path, "wb") as f:
                        for chunk in audio_generator:
                            if chunk:
                                f.write(chunk)
                else:
                    # Old API (v1.x)
                    from elevenlabs import set_api_key, generate, save
                    set_api_key(Config.ELEVENLABS_API_KEY)
                    audio = generate(
                        text=clean_text,
                        voice="Rachel",
                        model="eleven_multilingual_v2"
                    )
                    save(audio, output_path)
                
                print(f"✅ ElevenLabs audio generated: {output_path}")
                return output_path
            except Exception as e:
                print(f"⚠️ ElevenLabs error: {e}, falling back to gTTS")
                import traceback
                traceback.print_exc()
                # Fall through to gTTS
        else:
            if not ELEVENLABS_AVAILABLE:
                print("ℹ️ ElevenLabs package not installed, using gTTS")
            elif not Config.ELEVENLABS_API_KEY:
                print("ℹ️ ElevenLabs API key not found, using gTTS")
        
        # Fallback to gTTS
        if not GTTS_AVAILABLE or gTTS is None:
            raise ValueError("Neither ElevenLabs nor gTTS is available for TTS generation")
        
        tts = gTTS(text=clean_text, lang=language, slow=slow)
        tts.save(output_path)
        return output_path

    @staticmethod
    def generate_with_emotion(text: str, severity: str) -> str:
        """
        Generate audio with emotional tone based on severity using ElevenLabs
        Falls back to gTTS if ElevenLabs is not available
        """
        import time
        timestamp = int(time.time())
        filename = f"diagnosis_{severity}_{timestamp}.mp3"
        
        # Use ElevenLabs if available
        if ELEVENLABS_AVAILABLE and Config.ELEVENLABS_API_KEY:
            try:
                print(f"🎙️ Using ElevenLabs for TTS (severity: {severity})...")
                os.makedirs(Config.AUDIO_DIR, exist_ok=True)
                clean_text = TTSHandler._clean_text(text)
                output_path = os.path.join(Config.AUDIO_DIR, filename)
                
                # Map severity to voice and settings
                voice_settings = {
                    "serious": {
                        "voice": "Adam",  # More serious, authoritative
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "style": 0.3,
                        "use_speaker_boost": True
                    },
                    "moderate": {
                        "voice": "Rachel",  # Professional, clear
                        "stability": 0.6,
                        "similarity_boost": 0.7,
                        "style": 0.4,
                        "use_speaker_boost": True
                    },
                    "minor": {
                        "voice": "Bella",  # Calm, reassuring
                        "stability": 0.7,
                        "similarity_boost": 0.65,
                        "style": 0.2,
                        "use_speaker_boost": True
                    },
                    "uncertain": {
                        "voice": "Rachel",  # Professional, neutral
                        "stability": 0.6,
                        "similarity_boost": 0.7,
                        "style": 0.3,
                        "use_speaker_boost": True
                    }
                }
                
                settings = voice_settings.get(severity, voice_settings["moderate"])
                
                if ELEVENLABS_V2:
                    # New API (v2.x) - use text_to_speech.convert
                    # Voice IDs for common voices
                    voice_ids = {
                        "Adam": "pNInz6obpgDQGcFmaJgB",  # Adam
                        "Rachel": "21m00Tcm4TlvDq8ikWAM",  # Rachel
                        "Bella": "EXAVITQu4vr4xnSDxMaL"  # Bella
                    }
                    voice_id = voice_ids.get(settings["voice"], voice_ids["Rachel"])
                    
                    client = ElevenLabs(api_key=Config.ELEVENLABS_API_KEY)
                    audio_generator = client.text_to_speech.convert(
                        voice_id=voice_id,
                        text=clean_text,
                        model_id="eleven_multilingual_v2",
                        voice_settings=VoiceSettings(
                            stability=settings["stability"],
                            similarity_boost=settings["similarity_boost"],
                            style=settings["style"],
                            use_speaker_boost=settings["use_speaker_boost"]
                        )
                    )
                    # Save audio stream
                    with open(output_path, "wb") as f:
                        for chunk in audio_generator:
                            if chunk:
                                f.write(chunk)
                else:
                    # Old API (v1.x)
                    from elevenlabs import set_api_key, generate, save
                    set_api_key(Config.ELEVENLABS_API_KEY)
                    audio = generate(
                        text=clean_text,
                        voice=settings["voice"],
                        model="eleven_multilingual_v2",
                        voice_settings=VoiceSettings(
                            stability=settings["stability"],
                            similarity_boost=settings["similarity_boost"],
                            style=settings["style"],
                            use_speaker_boost=settings["use_speaker_boost"]
                        )
                    )
                    save(audio, output_path)
                
                print(f"✅ ElevenLabs audio generated with {settings['voice']} voice: {output_path}")
                return output_path
            except Exception as e:
                print(f"⚠️ ElevenLabs error: {e}, falling back to gTTS")
                import traceback
                traceback.print_exc()
                # Fall through to gTTS
        else:
            if not ELEVENLABS_AVAILABLE:
                print("ℹ️ ElevenLabs package not installed, using gTTS")
            elif not Config.ELEVENLABS_API_KEY:
                print("ℹ️ ElevenLabs API key not found, using gTTS")
        
        # Fallback to gTTS
        print("🎙️ Using gTTS for TTS generation...")
        slow = (severity in ["serious", "uncertain"])
        result = TTSHandler.generate_audio(text, filename, slow=slow)
        print(f"✅ gTTS audio generated: {result}")
        return result

