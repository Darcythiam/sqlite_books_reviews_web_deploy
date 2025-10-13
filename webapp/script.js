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

async function showAllBooks() {
  const res = await fetch("/api/books");
  const data = await res.json();
  renderShelf(data.books || []);
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

// initial load
showAllBooks();
