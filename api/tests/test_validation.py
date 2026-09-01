def test_get_validation(client):
    # Setup prediction
    pred_res = client.get("/predictions/MONDO:0005148?top_k=1")
    assert pred_res.status_code == 200
    pred_data = pred_res.json()
    pred_id = pred_data["predictions"][0]["id"]
    
    # Get validation
    res = client.get(f"/validation/{pred_id}")
    assert res.status_code == 200
    data = res.json()
    
    assert "prediction_id" in data
    assert data["prediction_id"] == pred_id
    assert "has_clinical_trial" in data
    assert "has_literature_support" in data
