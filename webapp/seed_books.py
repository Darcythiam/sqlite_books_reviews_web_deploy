import sqlite3, os, pathlib

DB = os.environ.get("APP_DATABASE", "db/books.db")
pathlib.Path("db").mkdir(exist_ok=True)

books = [
    ("Clean Code", "Robert C. Martin", 2008, "https://covers.openlibrary.org/b/isbn/9780132350884-L.jpg"),
    ("The Pragmatic Programmer", "Andrew Hunt; David Thomas", 1999, "https://covers.openlibrary.org/b/isbn/9780201616224-L.jpg"),
    ("Design Patterns", "Erich Gamma; Richard Helm; Ralph Johnson; John Vlissides", 1994, "https://covers.openlibrary.org/b/isbn/9780201633610-L.jpg"),
    ("Refactoring", "Martin Fowler", 1999, "https://covers.openlibrary.org/b/isbn/9780201485677-L.jpg"),
    ("Introduction to Algorithms", "Cormen; Leiserson; Rivest; Stein", 2009, "https://covers.openlibrary.org/b/isbn/9780262033848-L.jpg"),
    ("Code Complete", "Steve McConnell", 2004, "https://covers.openlibrary.org/b/isbn/9780735619678-L.jpg"),
    ("Cracking the Coding Interview", "Gayle Laakmann McDowell", 2015, "https://covers.openlibrary.org/b/isbn/9780984782857-L.jpg"),
    ("SICP", "Harold Abelson; Gerald Jay Sussman", 1996, "https://covers.openlibrary.org/b/isbn/9780262510875-L.jpg"),
    ("Working Effectively with Legacy Code", "Michael C. Feathers", 2004, "https://covers.openlibrary.org/b/isbn/9780131177055-L.jpg"),
    ("Head First Design Patterns", "Eric Freeman; Elisabeth Robson; Bert Bates; Kathy Sierra", 2004, "https://covers.openlibrary.org/b/isbn/9780596007126-L.jpg"),
]

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS Books (
    book_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    publication_year INTEGER,
    author TEXT DEFAULT '',
    image_url TEXT DEFAULT ''
);""")
for t, a, y, u in books:
    cur.execute("INSERT INTO Books (title, publication_year, author, image_url) VALUES (?, ?, ?, ?)",
                (t, y, a, u))
conn.commit()
conn.close()
print("Seeded 10 books.")
