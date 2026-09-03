def test_get_explanations(client):
    # Setup prediction
    pred_res = client.get("/predictions/MONDO:0005148?top_k=1")
    assert pred_res.status_code == 200
    pred_data = pred_res.json()
    pred_id = pred_data["predictions"][0]["id"]

    # Get explanations
    res = client.get(f"/explanations/{pred_id}")
    assert res.status_code == 200
    data = res.json()

    assert "prediction_id" in data
    assert data["prediction_id"] == pred_id
    assert "explanations" in data

    # We expect path_based and counterfactual depending on mocks
    methods = [ex["method"] for ex in data["explanations"]]
    assert len(methods) > 0
