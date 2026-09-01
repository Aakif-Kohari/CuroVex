def test_get_predictions(client):
    response = client.get("/predictions/MONDO:0005148?top_k=5")
    assert response.status_code == 200
    data = response.json()
    
    assert "id" in data
    assert data["disease_id"] == "MONDO:0005148"
    assert "model_version" in data
    assert "predictions" in data
    assert isinstance(data["predictions"], list)
    
    if len(data["predictions"]) > 0:
        pred = data["predictions"][0]
        assert "drug_id" in pred
        assert "score" in pred
        assert "rank" in pred
