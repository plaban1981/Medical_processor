"""Quick test script to verify POC setup"""

import os
import sys
from crew_orchestrator import run_medical_assessment
from utils.image_processor import ImageProcessor

def quick_test():
    print("\n" + "="*60)
    print("QUICK POC TEST")
    print("="*60)

    # Check for test images
    sample_dir = "data/sample_images"
    images = [f for f in os.listdir(sample_dir)
              if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    if not images:
        print("\n❌ No test images found!")
        print(f"   Add images to: {sample_dir}")
        return

    print(f"\n✅ Found {len(images)} test image(s)")

    # Test first image
    test_image = os.path.join(sample_dir, images[0])
    print(f"\n🔍 Testing with: {images[0]}")

    # Validate
    print("\n1. Validating image...")
    is_valid, msg = ImageProcessor.validate_image(test_image)
    print(f"   {msg}")

    if not is_valid:
        return

    # Run assessment
    print("\n2. Running assessment (this may take 60-90 seconds)...")
    print("   - Vision Agent analyzing...")
    print("   - Diagnostic Agent consulting PubMed...")
    print("   - Communication Agent preparing report...")

    try:
        result = run_medical_assessment(test_image)

        if 'error' in result:
            print(f"\n❌ Error: {result['error']}")
        else:
            print("\n✅ SUCCESS!")
            print("\n" + "="*60)
            print("RESULTS:")
            print("="*60)

            report = result.get('patient_report', {})
            print(f"\n📋 {report.get('summary', 'N/A')}")

            metadata = result.get('metadata', {})
            print(f"\n📊 Confidence: {metadata.get('confidence', 0)}%")

            diagnostic = result.get('diagnostic_analysis', {})
            if 'differential_diagnosis' in diagnostic:
                print(f"\n🔬 Top Diagnosis:")
                top = diagnostic['differential_diagnosis'][0]
                print(f"   {top['condition']} - {top['probability']}%")

            print(f"\n📚 Literature: {diagnostic.get('literature_count', 0)} studies")

            audio = report.get('audio_path')
            if audio:
                print(f"\n🎙️ Audio: {audio}")

            print("\n" + "="*60)
            print("✅ POC IS WORKING!")
            print("="*60)

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_test()

