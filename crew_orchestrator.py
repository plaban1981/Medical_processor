from crewai import Crew, Task, Process,LLM
from agents.vision_agent import create_vision_agent, VisionAgentHandler
from agents.diagnostic_agent import create_diagnostic_agent, DiagnosticAgentHandler
from agents.communication_agent import create_communication_agent, CommunicationAgentHandler
from utils.retry_handler import retry_with_exponential_backoff
from config.config import Config
from typing import Dict
import json

class MedicalAssessmentCrew:
    def __init__(self):
        # Initialize handlers
        self.vision_handler = VisionAgentHandler()
        self.diagnostic_handler = DiagnosticAgentHandler()
        self.communication_handler = CommunicationAgentHandler()

        # Create agents
        self.vision_agent = create_vision_agent()
        self.diagnostic_agent = create_diagnostic_agent()
        self.communication_agent = create_communication_agent()

        # Shared memory for context
        self.crew_memory = {}

    @retry_with_exponential_backoff(max_retries=Config.MAX_RETRIES)
    def assess_injury(self, image_path: str) -> Dict:
        """
        Main orchestration method - coordinates all agents
        Returns comprehensive assessment
        """
        print("🔍 Starting medical assessment...")

        # Step 1: Vision Agent Analysis
        print("\n✅ Vision Agent: Analyzing image...")
        vision_result = self._run_vision_analysis(image_path)
        self.crew_memory['vision_analysis'] = vision_result

        # Check image quality
        if vision_result['image_quality'] < 5:
            return {
                "error": "Image quality too low. Please upload a clearer photo.",
                "image_quality": vision_result['image_quality']
            }

        # Step 2: Diagnostic Agent Analysis
        print("\n🏥 Diagnostic Agent: Consulting medical literature...")
        diagnostic_result = self._run_diagnostic_analysis(vision_result)
        self.crew_memory['diagnostic_analysis'] = diagnostic_result

        # Step 3: Communication Agent Output
        print("\n🎙️ Communication Agent: Preparing patient report...")
        communication_result = self._run_communication_generation(diagnostic_result)

        # Compile final assessment
        final_assessment = {
            "vision_analysis": vision_result,
            "diagnostic_analysis": diagnostic_result,
            "patient_report": communication_result,
            "metadata": {
                "confidence": diagnostic_result.get('confidence', 0),
                "requires_professional_review": communication_result.get('requires_professional_review', True),
                "image_quality": vision_result['image_quality'],
                "crew_memory": self.crew_memory
            }
        }

        print("\n✅ Assessment complete!")
        return final_assessment

    def _run_vision_analysis(self, image_path: str) -> Dict:
        """Execute vision agent with retry logic"""
        try:
            result = self.vision_handler.analyze_image(image_path)

            # Create CrewAI task for structured processing
            vision_task = Task(
                description=f"""
                Process this medical image analysis and extract key structured data:

                Raw Analysis: {result['description']}

                Extract and structure:
                1. Injury type
                2. Key visible features
                3. Severity assessment
                4. Confidence level
                """,
                agent=self.vision_agent,
                expected_output="Structured JSON with injury analysis"
            )

            # Add structured data to result
            result['structured_analysis'] = result['description']
            return result

        except Exception as e:
            print(f"❌ Vision Agent error: {e}")
            raise

    def _run_diagnostic_analysis(self, vision_result: Dict) -> Dict:
        """Execute diagnostic agent with PubMed integration"""
        try:
            description = vision_result['description']

            # Search PubMed
            pubmed_results = self.diagnostic_handler.search_pubmed(
                description,
                max_results=10
            )

            # Generate differential diagnosis
            differential = self.diagnostic_handler.generate_differential_diagnosis(
                description,
                pubmed_results
            )

            # Create diagnostic task
            diagnostic_task = Task(
                description=f"""
                Based on this injury analysis:
                {description}

                And these medical literature findings:
                {json.dumps([r['title'] for r in pubmed_results[:5]], indent=2)}

                Provide:
                1. Most likely diagnosis
                2. Differential diagnoses (top 3)
                3. Recommended actions
                4. Warning signs to watch for
                """,
                agent=self.diagnostic_agent,
                expected_output="Evidence-based diagnostic assessment"
            )

            # Combine results
            result = {
                **differential,
                'pubmed_results': pubmed_results,
                'literature_count': len(pubmed_results)
            }

            return result

        except Exception as e:
            print(f"❌ Diagnostic Agent error: {e}")
            raise

    def _run_communication_generation(self, diagnostic_result: Dict) -> Dict:
        """Execute communication agent for patient output"""
        try:
            report = self.communication_handler.generate_patient_report(diagnostic_result)

            # Create communication task
            communication_task = Task(
                description=f"""
                Create a patient-friendly explanation of this diagnosis:

                Primary Diagnosis: {diagnostic_result.get('primary_diagnosis', {})}
                Confidence: {diagnostic_result.get('confidence', 0)}%

                Requirements:
                1. Use plain language (no medical jargon)
                2. Provide clear next steps
                3. Be empathetic and reassuring where appropriate
                4. Include appropriate warnings
                """,
                agent=self.communication_agent,
                expected_output="Patient-friendly report with clear guidance"
            )

            return report

        except Exception as e:
            print(f"❌ Communication Agent error: {e}")
            raise

    def get_crew_context(self) -> Dict:
        """Return shared crew memory for debugging"""
        return self.crew_memory


# Convenience function
def run_medical_assessment(image_path: str) -> Dict:
    """
    Main entry point for medical assessment
    """
    crew = MedicalAssessmentCrew()
    return crew.assess_injury(image_path)

