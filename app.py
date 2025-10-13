from flask import Flask, jsonify, render_template, request
import sqlite3, os

app = Flask(__name__)

# Allow tests/seed to override the DB path via env var
DATABASE = os.environ.get("APP_DATABASE", "db/books.db")

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
        return jsonify({"books": [dict(r) for r in rows]}), 200
    except Exception as e:
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
        return jsonify({"books": [dict(r) for r in rows]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
