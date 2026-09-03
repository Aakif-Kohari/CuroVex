from unittest.mock import MagicMock, patch

from validation.clinicaltrials_check import check_clinical_trials


@patch("validation.clinicaltrials_check.requests.get")
def test_finds_existing_trial(mock_get, mock_clinicaltrials_response):
    mock_resp = MagicMock()
    mock_resp.json.return_value = mock_clinicaltrials_response
    mock_get.return_value = mock_resp

    result = check_clinical_trials("Metformin", "Alzheimer")
    assert result.has_trial is True
    assert result.trial_count == 2
    assert len(result.trials) == 1

@patch("validation.clinicaltrials_check.requests.get")
def test_no_trial_found(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"totalCount": 0, "studies": []}
    mock_get.return_value = mock_resp

    result = check_clinical_trials("UnknownDrug", "UnknownDisease")
    assert result.has_trial is False
    assert result.trial_count == 0
    assert len(result.trials) == 0

@patch("validation.clinicaltrials_check.requests.get")
def test_parses_trial_details(mock_get, mock_clinicaltrials_response):
    mock_resp = MagicMock()
    mock_resp.json.return_value = mock_clinicaltrials_response
    mock_get.return_value = mock_resp

    result = check_clinical_trials("Metformin", "Alzheimer")
    trial = result.trials[0]
    assert trial["nctId"] == "NCT00000001"
    assert trial["title"] == "Mock Title 1"
    assert trial["status"] == "RECRUITING"

@patch("validation.clinicaltrials_check.requests.get")
def test_network_error_handled(mock_get):
    mock_get.side_effect = Exception("Network error")

    result = check_clinical_trials("Metformin", "Alzheimer")
    assert result.has_trial is False
    assert result.trial_count == 0
    assert len(result.trials) == 0

@patch("validation.clinicaltrials_check.requests.get")
def test_evidence_url_format(mock_get):
    mock_get.side_effect = Exception("Stop early")

    result = check_clinical_trials("Metformin", "Alzheimer")
    assert "intr=Metformin" in result.evidence_url
    assert "cond=Alzheimer" in result.evidence_url
