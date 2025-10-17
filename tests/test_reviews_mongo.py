# Integration test for MongoDB-backed Reviews API
# Verifies that reviews can be added and fetched correctly
# without affecting the real Atlas cluster.


import os
import pytest
from app import app, get_mongo, reviews_coll

@pytest.fixture
def client(monkeypatch):
    """
    Creates a test client and points MongoDB to a test database
    (so you don't use your live cluster data).
    """
    # Point to a temporary test database & collection
    monkeypatch.setenv("MONGODB_DB", "books_app_test")
    monkeypatch.setenv("MONGODB_REVIEWS_COLLECTION", "reviews_test")

    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

    # Cleanup test collection
    coll = reviews_coll()
    coll.delete_many({})


def test_add_and_list_reviews(client):
    """
    End-to-end test: Adds a review and retrieves it.
    """
    # 1. Add review
    payload = {
        "book_id": 123,
        "username": "Alice",
        "rating": 5,
        "review_text": "Fantastic book!"
    }
    res = client.post("/api/reviews", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert "review" in data
    assert data["review"]["username"] == "Alice"

    # 2. Retrieve reviews
    res = client.get("/api/reviews?book_id=123")
    assert res.status_code == 200
    data = res.get_json()
    assert "reviews" in data
    assert any(r["username"] == "Alice" for r in data["reviews"])


def test_invalid_review_missing_fields(client):
    """
    Verifies that backend rejects bad input.
    """
    res = client.post("/api/reviews", json={"username": "Bob"})
    data = res.get_json()
    assert res.status_code == 400
    assert "book_id" in data["error"]
