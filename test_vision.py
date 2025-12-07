"""Test vision agent image encoding and API call"""
import os
from agents.vision_agent import VisionAgentHandler
import base64
from PIL import Image

def test_vision():
    print("Testing Vision Agent...")
    
    # Get test image
    sample_dir = "data/sample_images"
    images = [f for f in os.listdir(sample_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not images:
        print("❌ No test images found!")
        return
    
    test_image = os.path.join(sample_dir, images[0])
    print(f"\nUsing image: {test_image}")
    
    # Test 1: Verify image can be opened
    print("\n1. Testing image file...")
    try:
        img = Image.open(test_image)
        print(f"   ✅ Image opened successfully")
        print(f"   Format: {img.format}")
        print(f"   Size: {img.size}")
        print(f"   Mode: {img.mode}")
    except Exception as e:
        print(f"   ❌ Failed to open image: {e}")
        return
    
    # Test 2: Verify base64 encoding
    print("\n2. Testing base64 encoding...")
    try:
        with open(test_image, "rb") as f:
            image_bytes = f.read()
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
        print(f"   ✅ Base64 encoded successfully")
        print(f"   Encoded length: {len(base64_image)} characters")
        print(f"   First 50 chars: {base64_image[:50]}...")
    except Exception as e:
        print(f"   ❌ Encoding failed: {e}")
        return
    
    # Test 3: Test vision agent
    print("\n3. Testing Vision Agent API call...")
    try:
        handler = VisionAgentHandler()
        print(f"   Model: {handler.model}")
        print(f"   Making API call...")
        
        result = handler.analyze_image(test_image)
        
        print(f"\n   ✅ API call successful!")
        print(f"   Response length: {len(result['description'])} characters")
        print(f"   Confidence: {result['confidence']}%")
        print(f"   Image quality: {result['image_quality']}/10")
        print(f"\n   First 300 chars of response:")
        print(f"   {result['description'][:300]}...")
        
        # Check if response indicates image wasn't seen
        if "can't" in result['description'].lower() or "cannot" in result['description'].lower() or "unable" in result['description'].lower():
            print(f"\n   ⚠️ WARNING: Response suggests image wasn't analyzed!")
            print(f"   This might indicate an encoding or API format issue.")
        
    except Exception as e:
        print(f"   ❌ Vision Agent failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vision()

