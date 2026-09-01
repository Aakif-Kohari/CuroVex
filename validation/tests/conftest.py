import pytest

@pytest.fixture
def mock_clinicaltrials_response():
    return {
        "totalCount": 2,
        "studies": [
            {
                "protocolSection": {
                    "identificationModule": {
                        "nctId": "NCT00000001",
                        "briefTitle": "Mock Title 1"
                    },
                    "designModule": {
                        "phases": ["PHASE1"]
                    },
                    "statusModule": {
                        "overallStatus": "RECRUITING"
                    }
                }
            }
        ]
    }

@pytest.fixture
def mock_pubmed_search_response():
    return {
        "esearchresult": {
            "count": "10",
            "idlist": ["12345", "67890"]
        }
    }

@pytest.fixture
def mock_pubmed_summary_response():
    return {
        "result": {
            "uids": ["12345", "67890"],
            "12345": {
                "title": "Article 1",
                "authors": [{"name": "Smith J"}],
                "pubdate": "2023 Jan 1",
                "source": "Journal X"
            },
            "67890": {
                "title": "Article 2",
                "authors": [{"name": "Doe J"}],
                "pubdate": "2023 Feb 1",
                "source": "Journal Y"
            }
        }
    }
