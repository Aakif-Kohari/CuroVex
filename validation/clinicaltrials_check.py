import os
import sys
import time
import logging
from dataclasses import dataclass, field
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ClinicalTrialResult:
    has_trial: bool
    trial_count: int
    trials: List[Dict[str, Any]] = field(default_factory=list)
    evidence_url: str = ""

def check_clinical_trials(drug_name: str, disease_name: str) -> ClinicalTrialResult:
    """
    Query ClinicalTrials.gov v2 API for trials involving the given drug and disease.
    """
    base_url = os.getenv("CLINICALTRIALS_API_BASE", "https://clinicaltrials.gov/api/v2")
    import urllib.parse
    enc_drug = urllib.parse.quote_plus(drug_name)
    enc_disease = urllib.parse.quote_plus(disease_name)
    evidence_url = f"https://clinicaltrials.gov/search?intr={enc_drug}&cond={enc_disease}"
    
    url = f"{base_url}/studies"
    params = {
        "query.intr": drug_name,
        "query.cond": disease_name,
        "pageSize": 5
    }

    try:
        time.sleep(1.0)
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        studies = data.get("studies", [])
        trial_count = data.get("totalCount", len(studies))
        
        trials = []
        for study in studies[:5]:
            protocol_section = study.get("protocolSection", {})
            identification = protocol_section.get("identificationModule", {})
            design = protocol_section.get("designModule", {})
            status_module = protocol_section.get("statusModule", {})
            
            trial = {
                "nctId": identification.get("nctId", ""),
                "title": identification.get("briefTitle", ""),
                "status": status_module.get("overallStatus", ""),
                "phase": design.get("phases", [])
            }
            trials.append(trial)
            
        return ClinicalTrialResult(
            has_trial=len(trials) > 0,
            trial_count=trial_count,
            trials=trials,
            evidence_url=evidence_url
        )
    except Exception as e:
        logger.error(f"Error querying ClinicalTrials.gov: {e}")
        return ClinicalTrialResult(
            has_trial=False,
            trial_count=0,
            trials=[],
            evidence_url=evidence_url
        )

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python clinicaltrials_check.py <drug_name> <disease_name>")
        sys.exit(1)
    
    drug = sys.argv[1]
    disease = sys.argv[2]
    result = check_clinical_trials(drug, disease)
    print(result)
