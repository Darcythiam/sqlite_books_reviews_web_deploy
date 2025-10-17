# 📚 Book Shelf Web Application  
### (SQLite + Flask + MongoDB Reviews)

A full-stack web application that allows users to **add, browse, and search books**, complete with **author names, cover images, and user reviews**.  
This project demonstrates integration between **Flask (Python)**, **SQLite** for structured book storage, and **MongoDB (Atlas)** for dynamic review management.

---

## 🚀 Features

### 🧩 Book Management (SQLite)
- Add new books with:
  - Title
  - Author
  - Publication year
  - Image URL (book cover)
- Display all books with modern card-style UI.
- Search books by **title** or **author** (real-time lookup).
- Data persisted locally in `books.db`.

### 💬 Review System (MongoDB)
- Add reviews (username, rating, comment) for any book.
- Fetch & display reviews under each book.
- Data stored securely in MongoDB Atlas (cloud cluster).
- Instant update of reviews without reloading the page.

### 🧠 Modern Design
- Grid-based shelf layout.
- Hover effects, rounded cards, smooth color contrast.
- Responsive & mobile-friendly.

### 🧪 Integration Tests
- SQLite tests for adding/searching books.
- MongoDB tests for adding/listing reviews.
- Isolated test DBs to ensure deterministic results.

---

## 🏗️ Tech Stack

| Layer | Technology | Purpose |
|--------|-------------|----------|
| Backend | Flask (Python) | API endpoints, routing |
| Database | SQLite | Persistent book records |
| Database | MongoDB Atlas | Dynamic reviews |
| Frontend | HTML, CSS, JavaScript | Book shelf interface |
| Testing | Pytest | Automated integration tests |

---

## ⚙️ Installation & Setup

### 1️⃣ Clone repository
```bash
git clone https://github.com/<yourusername>/toons-flag-chase.git
cd sqlite_books_reviews_web_example

```
---

## Run the app

python app.py

---


