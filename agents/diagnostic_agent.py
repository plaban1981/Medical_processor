from crewai import Agent, Task
import requests
from typing import List, Dict
from config.config import Config

class DiagnosticAgentHandler:
    def __init__(self):
        self.pubmed_base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    def search_pubmed(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search PubMed for medical literature
        Multi-pass refinement strategy
        """
        results = []

        # Extract keywords from the query (which might be a long description)
        broad_query = self._create_broad_query(query)
        print(f"PubMed query: {broad_query}")  # Debug output
        
        # Pass 1: Broad search
        broad_results = self._execute_search(broad_query, max_results)

        # Pass 2: Narrow to treatments (only if we have results)
        if broad_results:
            # Use the extracted keywords, not the full description
            narrow_query = f"{broad_query} AND treatment[Title/Abstract]"
            narrow_results = self._execute_search(narrow_query, max_results=5)
            results.extend(narrow_results)
        else:
            # If broad search failed, try with just the keywords
            results = broad_results

        # Prioritize meta-analyses and reviews
        results = self._prioritize_meta_analyses(results)

        return results[:max_results]

    def _create_broad_query(self, injury_description: str) -> str:
        """
        Convert injury description to structured medical search terms
        Extract only relevant medical keywords, ignore full sentences
        Focus on external injuries and wound care
        """
        keywords = []
        description_lower = injury_description.lower()

        # Expanded list of injury types - check for these terms
        injury_types = [
            "contusion", "laceration", "abrasion", "hematoma",
            "bruise", "wound", "burn", "fracture", "cut",
            "trauma", "injury", "sprain", "strain", "scrape"
        ]

        # Extract injury type keywords
        for injury_type in injury_types:
            if injury_type in description_lower:
                # Avoid duplicates
                if injury_type not in keywords:
                    keywords.append(injury_type)

        # If no specific terms found, use general terms
        if not keywords:
            keywords = ["wound", "injury", "trauma"]

        # Limit to top 2-3 most relevant terms
        keywords = keywords[:3]

        # Build query - Focus on general wound care for external injuries
        # Use more specific terms to get relevant wound care articles
        if len(keywords) > 1:
            injury_terms = " OR ".join(keywords[:2])
            # Focus on wound care, first aid, and general treatment
            query = f"({injury_terms}) AND (wound care OR first aid OR emergency treatment OR trauma care)"
        else:
            query = f"{keywords[0]} AND (wound care OR first aid)" if keywords else "wound care"
        
        return query

    def _execute_search(self, query: str, max_results: int) -> List[Dict]:
        """Execute PubMed E-utilities search"""
        try:
            # Search for article IDs
            search_url = f"{self.pubmed_base_url}esearch.fcgi"
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance",
                "usehistory": "y"
            }

            search_response = requests.get(search_url, params=search_params, timeout=15)
            
            # Check if request was successful
            if search_response.status_code != 200:
                print(f"PubMed API returned status {search_response.status_code}")
                return []
            
            search_data = search_response.json()
            
            # Debug: print query and response
            if not search_data.get("esearchresult"):
                print(f"Unexpected PubMed response structure: {list(search_data.keys())}")
                return []

            article_ids = search_data.get("esearchresult", {}).get("idlist", [])
            
            # Debug output
            if not article_ids:
                error_info = search_data.get('esearchresult', {}).get('errorlist', {})
                if error_info:
                    print(f"PubMed error: {error_info}")

            if not article_ids:
                return []

            # Fetch article summaries
            summary_url = f"{self.pubmed_base_url}esummary.fcgi"
            summary_params = {
                "db": "pubmed",
                "id": ",".join(article_ids),
                "retmode": "json"
            }

            summary_response = requests.get(summary_url, params=summary_params, timeout=10)
            summary_data = summary_response.json()

            # Parse results
            results = []
            for article_id in article_ids:
                article = summary_data.get("result", {}).get(article_id, {})
                if article:
                    results.append({
                        "pmid": article_id,
                        "title": article.get("title", ""),
                        "authors": article.get("authors", []),
                        "source": article.get("source", ""),
                        "pubdate": article.get("pubdate", ""),
                        "article_type": article.get("pubtype", [])
                    })

            return results

        except Exception as e:
            print(f"PubMed search error: {e}")
            return []

    def _prioritize_meta_analyses(self, results: List[Dict]) -> List[Dict]:
        """Prioritize meta-analyses and systematic reviews, filter irrelevant results"""
        meta_analyses = []
        relevant_other = []
        irrelevant = []

        # Terms that indicate irrelevant results (specific medical procedures/conditions)
        irrelevant_terms = [
            "perineal", "vaginal", "delivery", "obstetric", "childbirth",
            "tracheobronchial", "endotracheal", "intubation", "surgical procedure",
            "rotator cuff", "dermatitis", "eczema", "microdermabrasion", "cosmetic",
            "dermatology", "plastic surgery", "reconstructive", "endoscopic"
        ]
        
        # Terms that indicate relevant results (general wound care)
        relevant_terms = [
            "wound care", "first aid", "trauma", "emergency", "injury treatment",
            "laceration repair", "wound healing", "wound management", "trauma care"
        ]

        for result in results:
            title_lower = result.get("title", "").lower()
            
            # Filter out irrelevant results
            if any(term in title_lower for term in irrelevant_terms):
                irrelevant.append(result)
                continue
            
            # Prioritize results with relevant terms
            is_relevant = any(term in title_lower for term in relevant_terms)
            
            article_types = [t.lower() for t in result.get("article_type", [])]
            if "meta-analysis" in article_types or "systematic review" in article_types:
                meta_analyses.append(result)
            elif is_relevant:
                # Put relevant results first
                relevant_other.insert(0, result)
            else:
                relevant_other.append(result)

        # Return: meta-analyses first, then other relevant results
        # Irrelevant results are excluded
        return meta_analyses + relevant_other

    def generate_differential_diagnosis(self, vision_analysis: str, pubmed_results: List[Dict]) -> Dict:
        """
        Generate differential diagnosis with probabilities
        """
        # Extract likely conditions from vision analysis
        conditions = self._extract_conditions(vision_analysis)

        # Score based on literature support
        scored_conditions = []
        for condition in conditions[:Config.DIFFERENTIAL_DIAGNOSIS_COUNT]:
            literature_support = self._count_literature_support(condition, pubmed_results)
            literature_count = len([r for r in pubmed_results if condition.lower() in r.get("title", "").lower()])
            
            # Base probability even without literature (vision analysis confidence)
            # If we have literature, use it; otherwise give base score
            if literature_support > 0:
                base_probability = literature_support
            else:
                # Give base probability based on condition match in vision analysis
                # If condition appears in vision analysis, give it some weight
                condition_lower = condition.lower()
                if condition_lower in vision_analysis.lower():
                    base_probability = 40  # Base confidence from vision
                else:
                    base_probability = 20  # Lower confidence if not explicitly mentioned
            
            scored_conditions.append({
                "condition": condition,
                "probability": base_probability,
                "literature_count": len(pubmed_results) if literature_count == 0 and len(pubmed_results) > 0 else literature_count
            })

        # Normalize probabilities to sum to 100%
        total = sum(c["probability"] for c in scored_conditions)
        if total > 0:
            for condition in scored_conditions:
                condition["probability"] = round((condition["probability"] / total) * 100, 1)
        else:
            # Fallback: if all are 0, give equal distribution
            if scored_conditions:
                equal_prob = round(100.0 / len(scored_conditions), 1)
                for condition in scored_conditions:
                    condition["probability"] = equal_prob

        # Calculate overall confidence
        if scored_conditions:
            primary_prob = scored_conditions[0]["probability"]
            # Boost confidence if we have literature support
            lit_count = scored_conditions[0]["literature_count"]
            if lit_count > 0:
                # More literature = higher confidence boost
                boost = min(lit_count * 5, 25)  # Max 25% boost
                confidence = min(primary_prob + boost, 100)
            elif len(pubmed_results) > 0:
                # Even if no direct matches, having PubMed results is valuable
                confidence = min(primary_prob + 5, 100)
            else:
                confidence = primary_prob
        else:
            confidence = 50  # Default if no conditions found

        return {
            "differential_diagnosis": scored_conditions,
            "primary_diagnosis": scored_conditions[0] if scored_conditions else None,
            "confidence": confidence
        }

    def _extract_conditions(self, text: str) -> List[str]:
        """Extract potential medical conditions from text"""
        # Expanded list of injury terms
        common_conditions = [
            "contusion", "hematoma", "laceration", "abrasion",
            "bruise", "sprain", "strain", "fracture", "cut",
            "wound", "trauma", "injury", "scrape", "scratch"
        ]

        found = []
        text_lower = text.lower()

        # First pass: direct matches
        for condition in common_conditions:
            if condition in text_lower:
                # Avoid duplicates
                condition_cap = condition.capitalize()
                if condition_cap not in found:
                    found.append(condition_cap)

        # Second pass: fallback analysis using descriptive terms
        if not found:
            if any(word in text_lower for word in ["bleeding", "blood", "open", "cut", "laceration"]):
                found.append("Laceration")
            elif any(word in text_lower for word in ["bruise", "discoloration", "purple", "blue", "contusion"]):
                found.append("Contusion")
            elif any(word in text_lower for word in ["scrape", "surface", "abrade", "abrasion"]):
                found.append("Abrasion")
            elif any(word in text_lower for word in ["swelling", "hematoma", "bruise"]):
                found.append("Hematoma")

        return found if found else ["External injury"]

    def _count_literature_support(self, condition: str, results: List[Dict]) -> float:
        """Score condition based on literature support"""
        condition_lower = condition.lower()
        count = 0
        
        for r in results:
            title_lower = r.get("title", "").lower()
            # Check for exact match or related terms
            if condition_lower in title_lower:
                count += 1
            # Also check for related medical terms
            elif condition_lower == "laceration" and any(term in title_lower for term in ["tear", "cut", "wound"]):
                count += 0.5
            elif condition_lower == "abrasion" and any(term in title_lower for term in ["scrape", "scratch", "wound"]):
                count += 0.5
            elif condition_lower == "wound" and any(term in title_lower for term in ["injury", "trauma", "lesion"]):
                count += 0.5
        
        # If we have results but no direct matches, give some base score
        if count == 0 and len(results) > 0:
            # Having any literature results is better than none
            count = len(results) * 0.2
        
        return min(count * 20, 100)  # Cap at 100


def create_diagnostic_agent():
    """Create CrewAI Diagnostic Agent"""
    return Agent(
        role="Medical Diagnostic Specialist",
        goal="Analyze injury descriptions and provide evidence-based diagnosis using current medical literature",
        backstory="""You are a diagnostic medicine specialist with expertise in emergency medicine and wound care.
        You excel at differential diagnosis and evidence-based medicine.
        You always consult current medical literature to support your assessments.""",
        verbose=True,
        allow_delegation=False
    )

