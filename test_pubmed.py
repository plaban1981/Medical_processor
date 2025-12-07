"""Quick test to verify PubMed API is working"""
import requests

def test_pubmed():
    print("Testing PubMed API connectivity...")
    
    # Test 1: Simple search
    print("\n1. Testing simple search query...")
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": "laceration treatment",
        "retmax": 5,
        "retmode": "json"
    }
    
    try:
        response = requests.get(search_url, params=params, timeout=10)
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            article_ids = data.get("esearchresult", {}).get("idlist", [])
            print(f"   ✅ Found {len(article_ids)} articles")
            
            if article_ids:
                print(f"   Sample IDs: {article_ids[:3]}")
                
                # Test 2: Get summaries
                print("\n2. Testing summary retrieval...")
                summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                summary_params = {
                    "db": "pubmed",
                    "id": ",".join(article_ids[:3]),
                    "retmode": "json"
                }
                
                summary_response = requests.get(summary_url, params=summary_params, timeout=10)
                if summary_response.status_code == 200:
                    summary_data = summary_response.json()
                    print(f"   ✅ Retrieved summaries")
                    
                    # Show first result
                    first_id = article_ids[0]
                    article = summary_data.get("result", {}).get(first_id, {})
                    if article:
                        print(f"\n   Sample article:")
                        print(f"   Title: {article.get('title', 'N/A')[:80]}...")
                        print(f"   PMID: {article.get('uid', first_id)}")
                else:
                    print(f"   ❌ Summary request failed: {summary_response.status_code}")
            else:
                print("   ⚠️ No articles found - this might indicate an API issue")
        else:
            print(f"   ❌ Request failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out - check internet connection")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request error: {e}")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_pubmed()

