import os
import sys
import time
import logging
import urllib.parse
from dataclasses import dataclass, field
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PubMedResult:
    has_literature: bool
    article_count: int
    articles: List[Dict[str, Any]] = field(default_factory=list)
    evidence_url: str = ""

def check_pubmed(drug_name: str, disease_name: str) -> PubMedResult:
    base_url = os.getenv("PUBMED_API_BASE", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils")
    search_term = f'"{drug_name}" AND "{disease_name}"'
    encoded_term = urllib.parse.quote(search_term)
    evidence_url = f"https://pubmed.ncbi.nlm.nih.gov/?term={encoded_term}"
    
    try:
        # Search for IDs
        time.sleep(0.34)
        search_url = f"{base_url}/esearch.fcgi"
        search_params = {
            "db": "pubmed",
            "term": search_term,
            "retmode": "json",
            "retmax": 5
        }
        search_response = requests.get(search_url, params=search_params, timeout=10)
        search_response.raise_for_status()
        search_data = search_response.json()
        
        esearchresult = search_data.get("esearchresult", {})
        count = int(esearchresult.get("count", 0))
        id_list = esearchresult.get("idlist", [])
        
        if not id_list:
            return PubMedResult(
                has_literature=False,
                article_count=0,
                articles=[],
                evidence_url=evidence_url
            )
            
        # Get details
        time.sleep(0.34)
        summary_url = f"{base_url}/esummary.fcgi"
        summary_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "json"
        }
        summary_response = requests.get(summary_url, params=summary_params, timeout=10)
        summary_response.raise_for_status()
        summary_data = summary_response.json()
        
        result_dict = summary_data.get("result", {})
        articles = []
        for pmid in id_list:
            if pmid in result_dict:
                item = result_dict[pmid]
                authors = [a.get("name") for a in item.get("authors", [])]
                article = {
                    "pmid": pmid,
                    "title": item.get("title", ""),
                    "authors": authors,
                    "pub_date": item.get("pubdate", ""),
                    "source": item.get("source", "")
                }
                articles.append(article)
                
        return PubMedResult(
            has_literature=len(articles) > 0,
            article_count=count,
            articles=articles[:5],
            evidence_url=evidence_url
        )
        
    except Exception as e:
        logger.error(f"Error querying PubMed: {e}")
        return PubMedResult(
            has_literature=False,
            article_count=0,
            articles=[],
            evidence_url=evidence_url
        )

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python pubmed_check.py <drug_name> <disease_name>")
        sys.exit(1)
    
    drug = sys.argv[1]
    disease = sys.argv[2]
    result = check_pubmed(drug, disease)
    print(result)
