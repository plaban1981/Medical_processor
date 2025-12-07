"""Quick script to check which TTS service is configured"""
import os
from config.config import Config

print("="*60)
print("TTS SERVICE CHECK")
print("="*60)

# Check if ElevenLabs package is installed
try:
    from elevenlabs.client import ElevenLabs
    print("\n✅ ElevenLabs package: INSTALLED (v2.x API)")
    ELEVENLABS_AVAILABLE = True
    ELEVENLABS_V2 = True
except ImportError:
    try:
        from elevenlabs import generate, set_api_key
        print("\n✅ ElevenLabs package: INSTALLED (v1.x API)")
        ELEVENLABS_AVAILABLE = True
        ELEVENLABS_V2 = False
    except ImportError:
        print("\n❌ ElevenLabs package: NOT INSTALLED")
        print("   Install with: pip install elevenlabs")
        ELEVENLABS_AVAILABLE = False
        ELEVENLABS_V2 = False

# Check if gTTS is available
try:
    from gtts import gTTS
    print("✅ gTTS package: INSTALLED")
    GTTS_AVAILABLE = True
except ImportError:
    print("❌ gTTS package: NOT INSTALLED")
    GTTS_AVAILABLE = False

# Check API keys
print("\n" + "-"*60)
print("API KEYS:")
print("-"*60)

if Config.ELEVENLABS_API_KEY:
    # Mask the key for security
    masked_key = Config.ELEVENLABS_API_KEY[:10] + "..." + Config.ELEVENLABS_API_KEY[-4:] if len(Config.ELEVENLABS_API_KEY) > 14 else "***"
    print(f"✅ ElevenLabs API Key: {masked_key}")
else:
    print("❌ ElevenLabs API Key: NOT FOUND")
    print("   Add to .env: ELEVENLABS_API_KEY=your_key_here")

# Determine which service will be used
print("\n" + "-"*60)
print("TTS SERVICE STATUS:")
print("-"*60)

if ELEVENLABS_AVAILABLE and Config.ELEVENLABS_API_KEY:
    print("✅ ElevenLabs will be used for TTS")
    print("   - Better voice quality")
    print("   - Emotional tone control")
    print("   - Multiple voice options")
elif ELEVENLABS_AVAILABLE and not Config.ELEVENLABS_API_KEY:
    print("⚠️ ElevenLabs installed but API key missing")
    print("   → Will fallback to gTTS")
elif not ELEVENLABS_AVAILABLE and GTTS_AVAILABLE:
    print("ℹ️ gTTS will be used (ElevenLabs not installed)")
    print("   - Basic TTS functionality")
    print("   - No emotional tone control")
else:
    print("❌ No TTS service available!")
    print("   Install: pip install gtts")

print("\n" + "="*60)

