import os
import sqlite3
import pytest
from importlib import reload

# Schema identical to your real app
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS Books (
    book_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    publication_year INTEGER,
    author TEXT DEFAULT '',
    image_url TEXT DEFAULT ''
);
"""

@pytest.fixture()
def client(tmp_path, monkeypatch):
    """
    Creates a clean temporary SQLite database for each test.
    This prevents data leakage (e.g., duplicate rows) between runs.
    """
    # 1️⃣  Point APP_DATABASE to a temp file
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("APP_DATABASE", str(db_path))

    # 2️⃣  Re-import app so it reads the new env var
    import app as app_module
    reload(app_module)

    # 3️⃣  Initialize schema
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()

    # 4️⃣  Yield Flask test client
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c

# -----------------------------------------------------------------
# ✅ Example tests (your originals will remain, you can append more)
# -----------------------------------------------------------------

def test_add_book(client):
    """Adds a book and ensures it appears in list."""
    res = client.post("/api/add_book", json={
        "title": "The Pragmatic Programmer",
        "publication_year": 1999,
        "author": "Andrew Hunt",
        "image_url": "https://covers.openlibrary.org/b/isbn/9780201616224-L.jpg"
    })
    assert res.status_code == 201

    res = client.get("/api/books")
    books = res.get_json()["books"]
    assert len(books) == 1
    assert books[0]["title"] == "The Pragmatic Programmer"


def test_search_by_title(client):
    """Insert one title, verify search returns only that one."""
    # Insert directly into DB for isolation
    res = client.post("/api/add_book", json={
        "title": "The Pragmatic Programmer",
        "publication_year": 1999,
        "author": "Andrew Hunt",
        "image_url": "https://covers.openlibrary.org/b/isbn/9780201616224-L.jpg"
    })
    assert res.status_code == 201

    res = client.get("/api/search?q=Pragmatic")
    data = res.get_json()["books"]
    assert len(data) == 1
    assert data[0]["title"] == "The Pragmatic Programmer"
