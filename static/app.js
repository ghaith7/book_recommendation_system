const tabs = document.querySelectorAll(".tab");
const views = document.querySelectorAll(".view");

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((t) => {
      t.classList.remove("active");
      t.setAttribute("aria-selected", "false");
    });
    tab.classList.add("active");
    tab.setAttribute("aria-selected", "true");

    const target = tab.dataset.tab;
    views.forEach((v) => v.classList.toggle("active", v.id === target));
  });
});


const titleInput = document.getElementById("q-title");
const authorInput = document.getElementById("q-author");
const yearInput = document.getElementById("q-year");
const grid = document.getElementById("book-grid");
const resultCount = document.getElementById("result-count");
const emptyState = document.getElementById("empty-state");

let debounceTimer = null;

function debouncedSearch() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(fetchBooks, 200);
}

[titleInput, authorInput, yearInput].forEach((input) =>
  input.addEventListener("input", debouncedSearch)
);

async function fetchBooks() {
  const params = new URLSearchParams({
    title: titleInput.value.trim(),
    author: authorInput.value.trim(),
    year: yearInput.value.trim(),
  });

  try {
    const res = await fetch(`/api/books?${params.toString()}`);
    const data = await res.json();
    renderBooks(data.books);
  } catch (err) {
    resultCount.textContent = "Couldn't load books.";
    grid.innerHTML = "";
  }
}

function renderBooks(books) {
  grid.innerHTML = "";
  resultCount.textContent = `${books.length} book${books.length === 1 ? "" : "s"}`;
  emptyState.hidden = books.length !== 0;

  books.forEach((book) => {
    const card = document.createElement("article");
    card.className = "book-card";
    card.innerHTML = `
      <h2 class="book-title">${escapeHtml(book.title)}</h2>
      <p class="book-meta">${escapeHtml(book.author)} &middot; ${escapeHtml(book.pub_year)}</p>
      <p class="book-summary">${escapeHtml(book.summary)}</p>
    `;
    card.addEventListener("click", () => card.classList.toggle("expanded"));
    grid.appendChild(card);
  });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}


const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatLog = document.getElementById("chat-log");

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  appendMessage(message, "user");
  chatInput.value = "";

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await res.json();
    appendMessage(data.response, "bot");
  } catch (err) {
    appendMessage("Something went wrong reaching the recommendation service.", "bot");
  }
});

function appendMessage(text, who) {
  const bubble = document.createElement("div");
  bubble.className = `msg ${who}`;
  if (who === "bot") {
    bubble.innerHTML = text; 
  } else {
    bubble.textContent = text; 
  }
  chatLog.appendChild(bubble);
  chatLog.scrollTop = chatLog.scrollHeight;
}


fetchBooks();
