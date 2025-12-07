"""Debug the diagnostic process"""
from agents.vision_agent import VisionAgentHandler
from agents.diagnostic_agent import DiagnosticAgentHandler
import os

# Get test image
sample_dir = "data/sample_images"
images = [f for f in os.listdir(sample_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
if not images:
    print("❌ No test images found!")
    exit(1)

test_image = os.path.join(sample_dir, images[0])

print("="*60)
print("DIAGNOSTIC DEBUG")
print("="*60)

# Step 1: Vision Analysis
print("\n1️⃣ VISION ANALYSIS:")
print("-"*60)
vision_handler = VisionAgentHandler()
vision_result = vision_handler.analyze_image(test_image)

print(f"Description length: {len(vision_result['description'])} characters")
print(f"Confidence: {vision_result['confidence']}%")
print(f"\nFirst 500 chars of description:")
print(vision_result['description'][:500])
print("...")

# Step 2: Extract Conditions
print("\n2️⃣ CONDITION EXTRACTION:")
print("-"*60)
diagnostic_handler = DiagnosticAgentHandler()
conditions = diagnostic_handler._extract_conditions(vision_result['description'])
print(f"Extracted conditions: {conditions}")

if not conditions or conditions == ["Soft tissue injury"]:
    print("⚠️ PROBLEM: No specific conditions extracted!")
    print("The vision description may not contain common injury terms.")

# Step 3: PubMed Search
print("\n3️⃣ PUBMED SEARCH:")
print("-"*60)
print("Searching PubMed...")

pubmed_results = diagnostic_handler.search_pubmed(
    vision_result['description'],
    max_results=5
)

print(f"Found {len(pubmed_results)} studies")

if len(pubmed_results) == 0:
    print("⚠️ PROBLEM: No PubMed results!")
    print("This could be:")
    print("  - Internet connection issue")
    print("  - PubMed API not responding")
    print("  - Query too specific/vague")
    print(f"\nQuery used: {diagnostic_handler._create_broad_query(vision_result['description'])}")
else:
    print("\nTop results:")
    for i, result in enumerate(pubmed_results[:3], 1):
        print(f"\n{i}. {result['title'][:100]}...")
        print(f"   PMID: {result['pmid']}")

# Step 4: Differential Diagnosis
print("\n4️⃣ DIFFERENTIAL DIAGNOSIS:")
print("-"*60)

differential = diagnostic_handler.generate_differential_diagnosis(
    vision_result['description'],
    pubmed_results
)

print(f"\nPrimary diagnosis: {differential.get('primary_diagnosis')}")
print(f"Confidence: {differential.get('confidence')}%")
print(f"\nAll diagnoses:")
for diag in differential.get('differential_diagnosis', []):
    print(f"  - {diag['condition']}: {diag['probability']}% (lit: {diag['literature_count']})")

# Step 5: Identify Problem
print("\n5️⃣ ROOT CAUSE ANALYSIS:")
print("-"*60)

if differential.get('confidence', 0) == 0:
    print("❌ CONFIDENCE IS 0% BECAUSE:")

    if not conditions or conditions == ["Soft tissue injury"]:
        print("  1. Vision analysis doesn't mention specific injury types")
        print("     → Need to improve vision prompt or use better model")

    if len(pubmed_results) == 0:
        print("  2. PubMed search returned no results")
        print("     → Check internet connection or PubMed availability")

    if all(d['probability'] == 0 for d in differential.get('differential_diagnosis', [])):
        print("  3. No literature support for extracted conditions")
        print("     → Search terms don't match PubMed titles")

print("\n" + "="*60)

