from crewai import Agent
import os
from config.config import Config
from typing import Dict, List

class CommunicationAgentHandler:
    def __init__(self):
        os.makedirs(Config.AUDIO_DIR, exist_ok=True)

    def generate_patient_report(self, diagnosis_data: Dict) -> Dict:
        """
        Generate tiered patient-friendly report
        """
        differential = diagnosis_data.get("differential_diagnosis", [])
        primary = diagnosis_data.get("primary_diagnosis", {})
        confidence = diagnosis_data.get("confidence", 0)

        # Determine severity for emotional tone
        severity = self._determine_severity(confidence, primary)

        # Generate tiered text
        summary = self._generate_summary(primary, confidence, severity)
        detailed = self._generate_detailed(differential, confidence)
        medical = self._generate_medical_details(diagnosis_data)

        report = {
            "summary": summary,
            "detailed": detailed,
            "medical_details": medical,
            "severity": severity,
            "confidence": confidence,
            "requires_professional_review": confidence < Config.CONFIDENCE_THRESHOLD
        }

        # Generate audio
        audio_path = self._generate_audio(summary, severity)
        report["audio_path"] = audio_path

        return report

    def _determine_severity(self, confidence: float, primary_diagnosis: Dict) -> str:
        """Determine severity level"""
        if confidence < 50:
            return "uncertain"

        condition = primary_diagnosis.get("condition", "").lower() if primary_diagnosis else ""

        serious_conditions = ["fracture", "deep laceration", "severe burn"]
        if any(s in condition for s in serious_conditions):
            return "serious"

        moderate_conditions = ["laceration", "hematoma", "sprain"]
        if any(m in condition for m in moderate_conditions):
            return "moderate"

        return "minor"

    def _generate_summary(self, primary: Dict, confidence: float, severity: str) -> str:
        """Generate patient-friendly summary"""
        if not primary:
            return "Unable to determine injury type. Please consult a medical professional."

        condition = primary.get("condition", "Unknown injury")
        probability = primary.get("probability", 0)

        if severity == "serious":
            return f"⚠️ This appears to be a {condition} ({probability}% match). We recommend seeking medical attention promptly."
        elif severity == "moderate":
            return f"🟡 This appears to be a {condition} ({probability}% match). Consider consulting a healthcare provider if symptoms worsen."
        else:
            return f"🟢 This appears to be a minor {condition} ({probability}% match). Home care may be appropriate, but monitor for changes."

    def _generate_detailed(self, differential: List[Dict], confidence: float) -> str:
        """Generate detailed explanation"""
        if not differential:
            return "Insufficient information for detailed analysis."

        text = "**Detailed Assessment:**\n\n"
        text += "Based on the image analysis and current medical literature, here are the most likely diagnoses:\n\n"

        for i, condition in enumerate(differential, 1):
            text += f"{i}. **{condition['condition']}** - {condition['probability']}% likelihood\n"
            text += f"   - Supported by {condition['literature_count']} medical studies\n\n"

        if confidence < Config.CONFIDENCE_THRESHOLD:
            text += "\n⚠️ **Note:** Confidence is below our threshold. Professional evaluation recommended.\n"

        return text

    def _generate_medical_details(self, diagnosis_data: Dict) -> str:
        """Generate medical-grade details"""
        text = "**Medical Details:**\n\n"
        text += "**Diagnostic Approach:**\n"
        text += "- Image-based feature analysis\n"
        text += "- Literature-supported differential diagnosis\n"
        text += "- Evidence-based assessment\n\n"

        text += "**Recommendations:**\n"
        confidence = diagnosis_data.get("confidence", 0)

        if confidence >= 75:
            text += "- Monitor injury for 24-48 hours\n"
            text += "- Apply RICE protocol if applicable (Rest, Ice, Compression, Elevation)\n"
            text += "- Seek care if symptoms worsen\n"
        else:
            text += "- Professional medical evaluation recommended\n"
            text += "- Do not self-treat without professional guidance\n"
            text += "- Seek immediate care if pain increases or signs of infection appear\n"

        return text

    def _generate_audio(self, text: str, severity: str) -> str:
        """Generate TTS audio with emotional tone using ElevenLabs (with gTTS fallback)"""
        from utils.tts_handler import TTSHandler
        
        # Use TTSHandler which handles ElevenLabs with gTTS fallback
        import time
        timestamp = int(time.time())
        audio_filename = f"diagnosis_{severity}_{timestamp}.mp3"
        
        return TTSHandler.generate_with_emotion(text, severity)


def create_communication_agent():
    """Create CrewAI Communication Agent"""
    return Agent(
        role="Patient Communication Specialist",
        goal="Translate medical findings into clear, empathetic, accessible communication for patients",
        backstory="""You are a patient communication expert specializing in health literacy.
        You excel at explaining medical information in plain language while maintaining accuracy.
        You understand patient anxiety and communicate with empathy and clarity.""",
        verbose=True,
        allow_delegation=False
    )

