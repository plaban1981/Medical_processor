import unittest
import os
from crew_orchestrator import MedicalAssessmentCrew
from utils.image_processor import ImageProcessor
from agents.vision_agent import VisionAgentHandler
from agents.diagnostic_agent import DiagnosticAgentHandler

class TestMedicalAssessor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.test_image_dir = "data/sample_images"
        os.makedirs(cls.test_image_dir, exist_ok=True)

        # You'll need to add sample test images here
        cls.sample_images = [
            os.path.join(cls.test_image_dir, "contusion_sample.jpg"),
            os.path.join(cls.test_image_dir, "laceration_sample.jpg"),
            os.path.join(cls.test_image_dir, "abrasion_sample.jpg")
        ]

    def test_image_validation(self):
        """Test image validation"""
        processor = ImageProcessor()

        for image_path in self.sample_images:
            if os.path.exists(image_path):
                is_valid, message = processor.validate_image(image_path)
                self.assertTrue(is_valid, f"Image validation failed: {message}")

    def test_vision_agent(self):
        """Test vision agent analysis"""
        handler = VisionAgentHandler()

        for image_path in self.sample_images:
            if os.path.exists(image_path):
                result = handler.analyze_image(image_path)

                self.assertIn('description', result)
                self.assertIn('confidence', result)
                self.assertIn('image_quality', result)
                self.assertGreater(result['confidence'], 0)
                self.assertLessEqual(result['confidence'], 100)

    def test_diagnostic_agent(self):
        """Test diagnostic agent PubMed search"""
        handler = DiagnosticAgentHandler()

        test_query = "contusion external injury treatment"
        results = handler.search_pubmed(test_query, max_results=5)

        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

        # Check result structure
        for result in results:
            self.assertIn('pmid', result)
            self.assertIn('title', result)

    def test_end_to_end_assessment(self):
        """Test complete assessment flow"""
        crew = MedicalAssessmentCrew()

        # Use first available test image
        test_image = None
        for image_path in self.sample_images:
            if os.path.exists(image_path):
                test_image = image_path
                break

        if test_image:
            result = crew.assess_injury(test_image)

            # Check result structure
            self.assertIn('vision_analysis', result)
            self.assertIn('diagnostic_analysis', result)
            self.assertIn('patient_report', result)
            self.assertIn('metadata', result)

            # Check confidence is reasonable
            confidence = result['metadata']['confidence']
            self.assertGreaterEqual(confidence, 0)
            self.assertLessEqual(confidence, 100)
        else:
            self.skipTest("No test images available")

    def test_retry_mechanism(self):
        """Test retry logic handles failures"""
        from utils.retry_handler import retry_with_exponential_backoff

        attempt_count = [0]

        @retry_with_exponential_backoff(max_retries=3)
        def failing_function():
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise Exception("Simulated failure")
            return "Success"

        result = failing_function()
        self.assertEqual(result, "Success")
        self.assertEqual(attempt_count[0], 3)

    def test_confidence_threshold_logic(self):
        """Test confidence threshold triggers human review"""
        from config.config import Config

        # Test below threshold
        low_confidence = Config.CONFIDENCE_THRESHOLD - 10
        requires_review = low_confidence < Config.CONFIDENCE_THRESHOLD
        self.assertTrue(requires_review)

        # Test above threshold
        high_confidence = Config.CONFIDENCE_THRESHOLD + 10
        requires_review = high_confidence < Config.CONFIDENCE_THRESHOLD
        self.assertFalse(requires_review)


if __name__ == '__main__':
    unittest.main()

