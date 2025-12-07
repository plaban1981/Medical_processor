"""Test the actual PubMed query being generated"""
import requests

def test_query():
    # This is the query being generated
    query = "(laceration OR abrasion OR wound OR cut OR injury) AND (treatment OR management OR care)"
    
    print(f"Testing PubMed query: {query}")
    print("="*60)
    
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": 10,
        "retmode": "json",
        "sort": "relevance"
    }
    
    try:
        response = requests.get(search_url, params=search_params, timeout=15)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            article_ids = data.get("esearchresult", {}).get("idlist", [])
            total = data.get("esearchresult", {}).get("count", "0")
            
            print(f"Total results: {total}")
            print(f"Article IDs returned: {len(article_ids)}")
            
            if article_ids:
                print(f"\nFirst 5 IDs: {article_ids[:5]}")
                
                # Try to get summaries
                summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                summary_params = {
                    "db": "pubmed",
                    "id": ",".join(article_ids[:3]),
                    "retmode": "json"
                }
                
                summary_response = requests.get(summary_url, params=summary_params, timeout=10)
                if summary_response.status_code == 200:
                    summary_data = summary_response.json()
                    print("\nSample articles:")
                    for aid in article_ids[:3]:
                        article = summary_data.get("result", {}).get(aid, {})
                        if article:
                            print(f"\n  - {article.get('title', 'N/A')[:80]}...")
            else:
                print("\n⚠️ No results found!")
                print("Trying simpler query...")
                
                # Try simpler query
                simple_query = "laceration treatment"
                simple_params = {
                    "db": "pubmed",
                    "term": simple_query,
                    "retmax": 5,
                    "retmode": "json"
                }
                simple_response = requests.get(search_url, params=simple_params, timeout=10)
                if simple_response.status_code == 200:
                    simple_data = simple_response.json()
                    simple_ids = simple_data.get("esearchresult", {}).get("idlist", [])
                    print(f"Simple query '{simple_query}' returned {len(simple_ids)} results")
        else:
            print(f"Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_query()

