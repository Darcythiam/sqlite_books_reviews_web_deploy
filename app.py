import os, datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
import sqlite3, os

app = Flask(__name__)

# ----- MongoDB Setup (Reviews only) -----
load_dotenv()  # loads MONGODB_URI, etc. from .env if present

MONGO_URI = os.environ.get("MONGODB_URI")
MONGO_DB_NAME = os.environ.get("MONGODB_DB", "books_app")
MONGO_REVIEWS_COLL = os.environ.get("MONGODB_REVIEWS_COLLECTION", "reviews")

_mongo_client = None
def get_mongo():
    """Singleton Mongo client."""
    global _mongo_client
    if _mongo_client is None:
        if not MONGO_URI:
            raise RuntimeError("MONGODB_URI not set. Put it in .env or env vars.")
        _mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
        # triggers early failure if URI wrong
        _mongo_client.admin.command("ping")
    return _mongo_client

def reviews_coll():
    """Return the reviews collection handle."""
    client = get_mongo()
    return client[MONGO_DB_NAME][MONGO_REVIEWS_COLL]

def _review_to_json(doc):
    """Serialize Mongo Review doc to JSON serializable dict."""
    return {
        "_id": str(doc.get("_id")),
        "book_id": doc.get("book_id"),
        "username": doc.get("username"),
        "rating": doc.get("rating"),
        "review_text": doc.get("review_text"),
        "review_date": doc.get("review_date").isoformat() if doc.get("review_date") else None,
    }

# Allow tests/seed to override the DB path via env var
DATABASE = os.environ.get("APP_DATABASE", "db/books.db")

def log_event(details, message, level):
    """Log an event to the logs table."""
    try:
        conn = get_db()
        conn.execute("""
            INSERT INTO logs (details, message, level)
            VALUES (?, ?, ?)
        """, (details, message, level))
        conn.commit()
        conn.close()
    except Exception as e:
        #fallback: print to console
        print(f"Logging failed: {e}")

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    return render_template("index.html")

# List all books (explicit columns & stable order)
@app.route("/api/books", methods=["GET"])
def get_all_books():
    try:
        conn = get_db()
        rows = conn.execute("""
            SELECT book_id, title, publication_year, author, image_url
            FROM Books
            ORDER BY book_id DESC
        """).fetchall()
        conn.close()
        log_event("Fetched all books", f"Returned {len(rows)} books", "INFO")
        return jsonify({"books": [dict(r) for r in rows]}), 200
    except Exception as e:
        error_details = f"Error fetching all books: {e}"
        log_event(error_details, "Failed to fetch books", "ERROR")
        return jsonify({"error": str(e)}), 500

# Add a new book (title, author, image_url)
@app.route("/api/add_book", methods=["POST"])
def add_book():
    try:
        data = request.get_json(force=True)
        title = (data.get("title") or "").strip()
        publication_year = data.get("publication_year")
        author = data.get("author")
        image_url = data.get("image_url")

        if not title:
            return jsonify({"error": "Title is required"}), 400

        if publication_year not in (None, ""):
            try:
                publication_year = int(publication_year)
            except ValueError:
                return jsonify({"error": "publication_year must be an integer"}), 400
        else:
            publication_year = None

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Books (title, publication_year, author, image_url)
            VALUES (?, ?, ?, ?)
        """, (title, publication_year, author, image_url))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()

        log_event(f"Added book '{title}'", f"Book ID: {new_id}", "INFO")
        return jsonify({
            "message": "Book added successfully",
            "book": {
                "book_id": new_id,
                "title": title,
                "publication_year": publication_year,
                "author": author,
                "image_url": image_url
            }
        }), 201
    except Exception as e:
        error_details = f"Error adding book: {e}"
        log_event(error_details, "Failed to add book", "ERROR")
        return jsonify({"error": str(e)}), 500

# Search by title OR author
@app.route("/api/search", methods=["GET"])
def search_books():
    try:
        q = (request.args.get("q") or "").strip()
        if not q:
            return jsonify({"books": []}), 200
        like = f"%{q}%"
        conn = get_db()
        rows = conn.execute("""
            SELECT book_id, title, publication_year, author, image_url
            FROM Books
            WHERE title LIKE ? OR author LIKE ?
            ORDER BY book_id DESC
        """, (like, like)).fetchall()
        conn.close()

        log_event(f"Searched books with query '{q}'", f"Found {len(rows)} results", "INFO")
        return jsonify({"books": [dict(r) for r in rows]}), 200
    except Exception as e:
        error_details = f"Error searching books: {e}"
        log_event(error_details, "Failed to search books", "ERROR")
        return jsonify({"error": str(e)}), 500
    
# ---------------- Reviews: MongoDB-backed ----------------

@app.route("/api/reviews", methods=["GET"])
def list_reviews():
    """
    Get reviews for a given book.
    Query params:
      - book_id (required, int or str convertible to int)
    Example: /api/reviews?book_id=123
    """
    try:
        book_id = request.args.get("book_id")
        if not book_id:
            return jsonify({"error": "book_id is required"}), 400

        # normalize to int (your Books table uses INTEGER ids)
        try:
            book_id = int(book_id)
        except ValueError:
            return jsonify({"error": "book_id must be an integer"}), 400

        cur = reviews_coll().find(
            {"book_id": book_id},
            sort=[("review_date", -1), ("_id", -1)]
        )

        log_event(f"Fetched reviews for book_id {book_id}", "Success", "INFO")
        return jsonify({"reviews": [_review_to_json(d) for d in cur]}), 200
    except Exception as e:
        error_details = f"Error fetching reviews: {e}"
        log_event(error_details, "Failed to fetch reviews", "ERROR")
        return jsonify({"error": str(e)}), 500


@app.route("/api/reviews", methods=["POST"])
def create_review():
    """
    Add a new review for a book.
    Expected JSON:
      {
        "book_id": 123,                # required, int
        "username": "alice",           # required, str
        "rating": 5,                   # optional, int 0..5
        "review_text": "Great book!"   # optional, str
      }
    """
    try:
        data = request.get_json(force=True) or {}
        # book_id
        if "book_id" not in data or data.get("book_id") is None:
            return jsonify({"error": "book_id is required"}), 400
        try:
            book_id = (data.get("book_id"))
        except (TypeError, ValueError):
            return jsonify({"error": "book_id must be an integer"}), 400

        # username
        username = (data.get("username") or "").strip()
        if not username:
            return jsonify({"error": "username is required"}), 400

        # rating (optional)
        rating = data.get("rating")
        if rating not in (None, ""):
            try:
                rating = int(rating)
            except (TypeError, ValueError):
                return jsonify({"error": "rating must be an integer"}), 400
            if rating < 0 or rating > 5:
                return jsonify({"error": "rating must be between 0 and 5"}), 400
        else:
            rating = None

        # review_text (optional)
        review_text = (data.get("review_text") or "").strip() or None

        # assemble doc
        doc = {
            "book_id": book_id,
            "username": username,
            "rating": rating,
            "review_text": review_text,
            "review_date": datetime.datetime.utcnow(),
        }

        res = reviews_coll().insert_one(doc)
        doc["_id"] = res.inserted_id

        log_event(f"Added review for book_id {book_id} by user '{username}'", "Success", "INFO")
        return jsonify({"message": "Review added", "review": _review_to_json(doc)}), 201
    except Exception as e:
        error_details = f"Error creating review: {e}"
        log_event(error_details, "Failed to create review", "ERROR")
        return jsonify({"error": str(e)}), 500


@app.route("/api/reviews/<review_id>", methods=["DELETE"])
def delete_review(review_id):
    """
    Optional: delete a review by its Mongo _id for testing/demo.
    """
    try:
        oid = ObjectId(review_id)
    except Exception:
        return jsonify({"error": "Invalid review id"}), 400

    res = reviews_coll().delete_one({"_id": oid})
    if res.deleted_count == 0:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"message": "Deleted"}), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
