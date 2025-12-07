"""
Manual testing script for POC validation
Run this to test each component individually
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from crew_orchestrator import run_medical_assessment
from utils.image_processor import ImageProcessor
import json

def test_sample_image(image_path):
    """Test with a single image"""
    print(f"\n{'='*60}")
    print(f"Testing with image: {image_path}")
    print(f"{'='*60}\n")

    # Validate image
    print("1. Validating image...")
    is_valid, message = ImageProcessor.validate_image(image_path)
    print(f"   Result: {message}")

    if not is_valid:
        print("   ❌ Image validation failed. Stopping.")
        return

    # Run assessment
    print("\n2. Running full assessment...")
    try:
        result = run_medical_assessment(image_path)

        # Display results
        print("\n3. Assessment Results:")
        print(f"   {'='*50}")

        if 'error' in result:
            print(f"   ❌ Error: {result['error']}")
        else:
            # Summary
            report = result.get('patient_report', {})
            print(f"\n   📋 SUMMARY:")
            print(f"   {report.get('summary', 'N/A')}")

            # Confidence
            metadata = result.get('metadata', {})
            confidence = metadata.get('confidence', 0)
            print(f"\n   📊 CONFIDENCE: {confidence}%")

            # Professional review flag
            if metadata.get('requires_professional_review'):
                print(f"   ⚠️  Professional review recommended")

            # Differential diagnosis
            diagnostic = result.get('diagnostic_analysis', {})
            if 'differential_diagnosis' in diagnostic:
                print(f"\n   🔬 DIFFERENTIAL DIAGNOSIS:")
                for i, condition in enumerate(diagnostic['differential_diagnosis'], 1):
                    print(f"      {i}. {condition['condition']} - {condition['probability']}%")

            # Literature
            literature_count = diagnostic.get('literature_count', 0)
            print(f"\n   📚 LITERATURE: {literature_count} studies consulted")

            # Audio
            audio_path = report.get('audio_path')
            if audio_path:
                print(f"\n   🎙️  AUDIO: Generated at {audio_path}")

        print(f"\n   {'='*50}")

        # Save full result
        output_file = "test_result.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n   💾 Full results saved to: {output_file}")

        print("\n✅ Test completed successfully!")

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    print("\n" + "="*60)
    print(" MEDICAL ASSESSOR POC - MANUAL TEST SCRIPT")
    print("="*60)

    # Check for test images
    sample_dir = "data/sample_images"

    if not os.path.exists(sample_dir):
        print(f"\n❌ Sample images directory not found: {sample_dir}")
        print("   Please create it and add test images.")
        return

    # List available images
    images = [f for f in os.listdir(sample_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    if not images:
        print(f"\n❌ No test images found in: {sample_dir}")
        print("   Please add some injury photos for testing.")
        return

    print(f"\nFound {len(images)} test image(s):")
    for i, img in enumerate(images, 1):
        print(f"   {i}. {img}")

    # Test each image
    for image_file in images:
        image_path = os.path.join(sample_dir, image_file)
        test_sample_image(image_path)

        if len(images) > 1:
            input("\nPress Enter to test next image...")


if __name__ == "__main__":
    main()

