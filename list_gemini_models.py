"""List available Gemini models"""
import google.generativeai as genai
from config.config import Config

if not Config.GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not found!")
    exit(1)

genai.configure(api_key=Config.GEMINI_API_KEY)

print("Fetching available Gemini models...")
print("="*60)

try:
    models = genai.list_models()
    
    print("\nAvailable models that support vision/image analysis:\n")
    
    vision_models = []
    for model in models:
        # Check if model supports generateContent and has vision capabilities
        if 'generateContent' in model.supported_generation_methods:
            # Check if it's a vision-capable model
            model_name = model.name.replace('models/', '')
            if 'vision' in model_name.lower() or 'gemini' in model_name.lower():
                vision_models.append(model_name)
                print(f"✅ {model_name}")
                print(f"   Display Name: {model.display_name}")
                print(f"   Description: {model.description[:100] if model.description else 'N/A'}...")
                print()
    
    if not vision_models:
        print("No vision models found. Listing all available models:\n")
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                print(f"  - {model.name.replace('models/', '')}")
    
    print("\n" + "="*60)
    print(f"\nRecommended model for vision: gemini-1.5-pro or gemini-1.5-flash")
    
except Exception as e:
    print(f"❌ Error listing models: {e}")

