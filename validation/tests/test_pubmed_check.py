from unittest.mock import MagicMock, patch

from validation.pubmed_check import check_pubmed


@patch("validation.pubmed_check.requests.get")
def test_finds_existing_literature(mock_get, mock_pubmed_search_response, mock_pubmed_summary_response):
    mock_search = MagicMock()
    mock_search.json.return_value = mock_pubmed_search_response
    mock_summary = MagicMock()
    mock_summary.json.return_value = mock_pubmed_summary_response
    
    mock_get.side_effect = [mock_search, mock_summary]

    result = check_pubmed("Metformin", "Alzheimer")
    assert result.has_literature is True
    assert result.article_count == 10
    assert len(result.articles) == 2

@patch("validation.pubmed_check.requests.get")
def test_no_literature_found(mock_get):
    mock_search = MagicMock()
    mock_search.json.return_value = {"esearchresult": {"count": "0", "idlist": []}}
    mock_get.return_value = mock_search

    result = check_pubmed("UnknownDrug", "UnknownDisease")
    assert result.has_literature is False
    assert result.article_count == 0
    assert len(result.articles) == 0

@patch("validation.pubmed_check.requests.get")
def test_parses_article_details(mock_get, mock_pubmed_search_response, mock_pubmed_summary_response):
    mock_search = MagicMock()
    mock_search.json.return_value = mock_pubmed_search_response
    mock_summary = MagicMock()
    mock_summary.json.return_value = mock_pubmed_summary_response
    
    mock_get.side_effect = [mock_search, mock_summary]

    result = check_pubmed("Metformin", "Alzheimer")
    article = result.articles[0]
    assert article["pmid"] == "12345"
    assert article["title"] == "Article 1"
    assert article["authors"] == ["Smith J"]

@patch("validation.pubmed_check.requests.get")
def test_network_error_handled(mock_get):
    mock_get.side_effect = Exception("Network error")

    result = check_pubmed("Metformin", "Alzheimer")
    assert result.has_literature is False
    assert result.article_count == 0
    assert len(result.articles) == 0

@patch("validation.pubmed_check.requests.get")
def test_limits_to_five_articles(mock_get):
    mock_search = MagicMock()
    mock_search.json.return_value = {
        "esearchresult": {
            "count": "10",
            "idlist": ["1", "2", "3", "4", "5", "6"]
        }
    }
    
    result_dict = {"uids": ["1", "2", "3", "4", "5", "6"]}
    for i in range(1, 7):
        result_dict[str(i)] = {"title": f"Article {i}"}
        
    mock_summary = MagicMock()
    mock_summary.json.return_value = {"result": result_dict}
    
    mock_get.side_effect = [mock_search, mock_summary]

    result = check_pubmed("Metformin", "Alzheimer")
    assert result.has_literature is True
    assert len(result.articles) == 5
