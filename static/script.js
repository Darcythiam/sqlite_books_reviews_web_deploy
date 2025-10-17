// Render a single book as a polished card
function bookCardHTML(b) {
  const img = b.image_url && b.image_url.trim()
    ? b.image_url.trim()
    : "https://via.placeholder.com/400x600?text=No+Image";
  const year = (b.publication_year !== null && b.publication_year !== undefined && `${b.publication_year}`.trim() !== "")
    ? ` • ${b.publication_year}`
    : "";
  return `
    <article class="card">
      <img class="cover"
           src="${img}"
           alt="Cover of ${b.title || 'book'}"
           referrerpolicy="no-referrer"
           onerror="this.onerror=null;this.src='https://via.placeholder.com/400x600?text=Image+Blocked';" />
      <h3 class="title">${b.title || 'Untitled'}</h3>
      <p class="meta">${b.author || '—'}${year}</p>
    </article>
  `;
}

function renderShelf(list, targetId = "allbooks") {
  const el = document.getElementById(targetId);
  el.innerHTML = (list || []).map(bookCardHTML).join("");
}

function bookCardHTML(b) {
  const img = b.image_url && b.image_url.trim()
    ? b.image_url.trim()
    : "https://via.placeholder.com/200x300?text=No+Image";
  const author = b.Author_Name || b.author || "—";
  const year = b.publication_year || "—";

  return `
    <article class="card">
      <img class="cover"
           src="${img}"
           alt="Cover of ${b.title}"
           style="width:200px;height:300px;object-fit:cover;border-radius:8px;"
           referrerpolicy="no-referrer"
           onerror="this.onerror=null;this.src='https://via.placeholder.com/200x300?text=Image+Blocked';"/>
      <h3>${b.title}</h3>
      <p>${author} • ${year}</p>

      <div class="reviews-panel">
        <input id="rv-user-${b.book_id}" placeholder="Your name" />
        <input id="rv-rating-${b.book_id}" type="number" min="0" max="5" placeholder="Rating" />
        <textarea id="rv-text-${b.book_id}" placeholder="Write review..."></textarea>
        <button onclick="addReview(${b.book_id})">Add Review</button>
        <button onclick="loadReviews(${b.book_id})">Show Reviews</button>
        <div id="reviews-${b.book_id}" class="reviews-list muted">No reviews yet.</div>
      </div>
    </article>
  `;
}

async function showAllBooks() {
  const res = await fetch('/api/books');
  const data = await res.json();
  const bookList = document.getElementById('allbooks');
  bookList.innerHTML = (data.books || []).map(bookCardHTML).join("");
}

async function searchBooks() {
  const q = document.getElementById("searchInput").value.trim();
  if (!q) { showAllBooks(); return; }
  const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
  const data = await res.json();
  renderShelf(data.books || []);
}

async function addBook() {
  const title = document.getElementById("bookTitle").value.trim();
  const author = document.getElementById("author").value.trim();
  const publication_year = document.getElementById("publicationYear").value.trim();
  const image_url = document.getElementById("image_url").value.trim();

  const payload = { title, author, publication_year, image_url };

  const res = await fetch("/api/add_book", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const out = await res.json();
  if (out.error) { alert(out.error); return; }

  document.getElementById("bookList").innerText =
    `Added: ${title}${author ? ' by ' + author : ''}`;
  // Clear inputs
  document.getElementById("bookTitle").value = "";
  document.getElementById("author").value = "";
  document.getElementById("publicationYear").value = "";
  document.getElementById("image_url").value = "";

  // refresh shelf
  showAllBooks();
}
// ----- Reviews (MongoDB) helpers -----

async function loadReviews(bookId) {
  const box = document.getElementById(`reviews-${bookId}`);
  if (!box) return;
  box.innerHTML = "<div class='muted'>Loading reviews…</div>";
  try {
    const res = await fetch(`/api/reviews?book_id=${encodeURIComponent(bookId)}`);
    const data = await res.json();
    const items = (data.reviews || []).map(r => `
      <div class="review-item">
        <div class="review-head"><strong>${escapeHtml(r.username || 'Anonymous')}</strong>${r.rating != null ? ` • ${r.rating}/5` : ''}</div>
        <div class="review-text">${escapeHtml(r.review_text || '')}</div>
        <div class="review-date muted">${r.review_date ? new Date(r.review_date).toLocaleString() : ''}</div>
      </div>
    `).join("") || "<div class='muted'>No reviews yet.</div>";
    box.innerHTML = items;
  } catch (err) {
    box.innerHTML = `<div class='muted'>Failed to load reviews.</div>`;
    console.error(err);
  }
}

async function addReview(bookId) {
  const userEl = document.getElementById(`rv-user-${bookId}`);
  const ratingEl = document.getElementById(`rv-rating-${bookId}`);
  const textEl = document.getElementById(`rv-text-${bookId}`);

  const username = (userEl?.value || "").trim();
  const rating = (ratingEl?.value || "").trim();
  const review_text = (textEl?.value || "").trim();

  const payload = { book_id: bookId, username, rating, review_text };

  try {
    const res = await fetch("/api/reviews", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const out = await res.json();
    if (out.error) { alert(out.error); return; }

    // Clear inputs and refresh list
    if (userEl) userEl.value = "";
    if (ratingEl) ratingEl.value = "";
    if (textEl) textEl.value = "";
    loadReviews(bookId);
  } catch (err) {
    alert("Failed to add review.");
    console.error(err);
  }
}

// tiny XSS-safe helper for review text/user
function escapeHtml(s) {
  return (s || "").replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
