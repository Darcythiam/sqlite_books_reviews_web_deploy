import os, sqlite3, tempfile, json
import pytest
from app import app as flask_app

SCHEMA = """
CREATE TABLE IF NOT EXISTS Books (
    book_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    publication_year INTEGER,
    author TEXT DEFAULT '',
    image_url TEXT DEFAULT ''
);
"""

@pytest.fixture()
def client():
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)
    flask_app.config["TESTING"] = True
    flask_app.config["DATABASE"] = db_path

    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()

    with flask_app.test_client() as client:
        yield client

    os.remove(db_path)

def test_add_book_stores_all_fields(client):
    payload = {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "publication_year": 2008,
        "image_url": "https://covers.openlibrary.org/b/isbn/9780132350884-L.jpg"
    }
    res = client.post("/api/add_book", data=json.dumps(payload), content_type="application/json")
    assert res.status_code in (200, 201)

    res = client.get("/api/books")
    data = res.get_json()
    assert "books" in data
    assert any(b["title"] == "Clean Code" and
               b["author"] == "Robert C. Martin" and
               "openlibrary" in (b["image_url"] or "")
               for b in data["books"])

def test_search_by_title(client):
    client.post("/api/add_book", data=json.dumps({
        "title": "The Pragmatic Programmer", "author": "Andrew Hunt",
        "publication_year": 1999, "image_url": "https://covers.openlibrary.org/b/isbn/9780201616224-L.jpg"
    }), content_type="application/json")

    res = client.get("/api/search?q=Pragmatic")
    books = res.get_json()["books"]
    assert len(books) == 1
    assert books[0]["title"] == "The Pragmatic Programmer"

def test_search_by_author(client):
    client.post("/api/add_book", data=json.dumps({
        "title": "Design Patterns", "author": "Erich Gamma",
        "publication_year": 1994, "image_url": "https://covers.openlibrary.org/b/isbn/9780201633610-L.jpg"
    }), content_type="application/json")

    res = client.get("/api/search?q=Gamma")
    books = res.get_json()["books"]
    assert len(books) >= 1
    assert any("Design Patterns" == b["title"] for b in books)

def test_search_nonexistent_returns_empty(client):
    res = client.get("/api/search?q=this-will-not-exist-xyz")
    data = res.get_json()
    assert data["books"] == []
