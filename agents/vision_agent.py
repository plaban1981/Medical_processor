import google.generativeai as genai
from crewai import Agent, Task
from config.config import Config
from PIL import Image

class VisionAgentHandler:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables or .env file")
        genai.configure(api_key=Config.GEMINI_API_KEY)
        # Use model name without 'models/' prefix - the SDK handles it
        model_name = Config.GEMINI_VISION_MODEL.replace('models/', '')
        self.model = genai.GenerativeModel(model_name)

    def analyze_image(self, image_path):
        """
        Analyze injury image and return structured description using Gemini Pro
        """
        # Verify image exists and can be opened
        try:
            img = Image.open(image_path)
            # Convert to RGB if necessary (Gemini works best with RGB)
            if img.mode != 'RGB':
                img = img.convert('RGB')
        except Exception as e:
            raise ValueError(f"Invalid image file: {e}")

        # Resize image if too large (Gemini has size limits)
        # Max dimension should be around 2048px for best results
        max_dimension = 2048
        if img.size[0] > max_dimension or img.size[1] > max_dimension:
            img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

        # Create detailed prompt for medical analysis
        prompt = """You are a medical image analysis assistant for an educational research tool. This is a proof-of-concept system for analyzing external injuries in photographs for educational and research purposes only.

Please analyze the injury photograph provided with this message. Look at the image carefully and describe what you observe.

Provide your analysis in this structured format:

1. INJURY TYPE: [State the specific type of injury visible - laceration, abrasion, contusion, hematoma, bruise, scrape, etc.]

2. VISIBLE FEATURES:
   - Color/discoloration: [Describe the colors you see - red, purple, blue, yellow, etc.]
   - Size/dimensions: [Estimate size in cm if possible, or relative size]
   - Texture: [smooth, rough, raised, flat, etc.]
   - Location on body: [if identifiable from the image - arm, leg, hand, etc.]
   - Swelling present: [yes/no and severity if yes]
   - Open wound: [yes/no - is the skin broken?]
   - Bleeding: [yes/no - is there visible blood?]

3. SEVERITY ASSESSMENT: [Minor, Moderate, or Severe] - [brief reasoning for your assessment]

4. IMAGE QUALITY: [Rate 1-10] - [brief comment on clarity, lighting, angle, focus]

5. CONFIDENCE: [Your confidence percentage]% - [brief explanation of how certain you are]

IMPORTANT: Please analyze the image that is attached to this message. Describe the visible characteristics of the injury you observe in the photograph. This analysis is for educational purposes only."""

        # Generate analysis using Gemini Vision API
        try:
            response = self.model.generate_content([prompt, img])
            response_text = response.text
            
            # Debug: Check if we got a valid response
            if not response_text or len(response_text) < 50:
                print(f"⚠️ Warning: Short response from vision model: {response_text[:100]}")
            
        except Exception as e:
            print(f"❌ Error calling Gemini Vision API: {e}")
            raise

        return {
            "description": response_text,
            "image_quality": self._extract_quality(response_text),
            "confidence": self._extract_confidence(response_text)
        }

    def _extract_confidence(self, text):
        """Extract confidence percentage from response"""
        import re
        match = re.search(r'CONFIDENCE.*?(\d+)%', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 70  # Default if not found

    def _extract_quality(self, text):
        """Extract image quality score"""
        import re
        match = re.search(r'IMAGE QUALITY.*?(\d+)', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 7  # Default


def create_vision_agent():
    """Create CrewAI Vision Agent"""
    return Agent(
        role="Medical Vision Analyst",
        goal="Analyze injury photographs and provide detailed, structured descriptions of visible injuries",
        backstory="""You are an expert medical image analyst specializing in external injuries.
        You have extensive training in identifying wound types, severity assessment, and clinical description.
        You provide precise, objective observations while noting any uncertainty.""",
        verbose=True,
        allow_delegation=False
    )

