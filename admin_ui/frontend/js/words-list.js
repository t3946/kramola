import { Grid, html } from "gridjs";

const DEBOUNCE_MS = 300;

/**
 * @param {string} s
 * @returns {string}
 */
function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

/**
 * @param {string} text
 * @param {string} searchTerm
 * @returns {string} HTML with highlighted matches
 */
function highlightSearch(text, searchTerm) {
  if (!searchTerm) return escapeHtml(text);
  const escapedSearch = searchTerm.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const re = new RegExp("(" + escapedSearch + ")", "gi");
  const parts = text.split(re);
  return parts
    .map((part, i) =>
      i % 2 === 1
        ? '<span class="search-highlight">' + escapeHtml(part) + "</span>"
        : escapeHtml(part)
    )
    .join("");
}

/**
 * @param {{ phrase: string, edit_url: string, delete_url: string }} row
 * @returns {string}
 */
function actionsHtml(row) {
  const phraseEsc = escapeHtml(row.phrase);
  return (
    '<button type="button" class="btn btn-sm btn-outline-primary gridjs-btn" title="Изменить" data-edit-url="' +
    escapeHtml(row.edit_url) +
    '" data-phrase="' +
    phraseEsc +
    '"><i class="fa fa-pencil"></i></button> ' +
    '<button type="button" class="btn btn-sm btn-outline-danger gridjs-btn" title="Удалить" data-delete-url="' +
    escapeHtml(row.delete_url) +
    '" data-phrase="' +
    phraseEsc +
    '"><i class="fa fa-trash"></i></button>'
  );
}

function initWordsList() {
  document.querySelectorAll("[data-modal-open]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-modal-open");
      if (id) document.getElementById(id).classList.remove("hidden");
    });
  });
  document.querySelectorAll("[data-modal-close]").forEach((el) => {
    el.addEventListener("click", () => {
      const id = el.getAttribute("data-modal-close");
      if (id) document.getElementById(id).classList.add("hidden");
    });
  });

  const wrapper = document.getElementById("words-grid-wrapper");
  const searchEl = document.getElementById("word-search");
  const dataUrl = searchEl?.getAttribute("data-data-url");
  if (!dataUrl || !wrapper) return;

  let debounceTimer = null;
  let currentGrid = null;

  wrapper.addEventListener("click", (e) => {
    const editBtn = e.target.closest("button[data-edit-url]");
    if (editBtn) {
      const form = document.getElementById("edit-phrase-form");
      const input = document.getElementById("edit-phrase-input");
      if (form && input) {
        form.action = editBtn.getAttribute("data-edit-url");
        input.value = editBtn.getAttribute("data-phrase") || "";
        document.getElementById("edit-phrase-modal").classList.remove("hidden");
      }
      return;
    }
    const delBtn = e.target.closest("button[data-delete-url]");
    if (delBtn) {
      const form = document.getElementById("delete-phrase-form");
      const message = document.getElementById("delete-phrase-message");
      if (form && message) {
        form.action = delBtn.getAttribute("data-delete-url");
        message.textContent =
          "Удалить фразу «" + (delBtn.getAttribute("data-phrase") || "") + "» из списка?";
        document.getElementById("delete-phrase-modal").classList.remove("hidden");
      }
    }
  });

  /**
   * @returns {string}
   */
  function buildServerUrl() {
    const q = searchEl?.value.trim();
    const sep = dataUrl.indexOf("?") >= 0 ? "&" : "?";
    return dataUrl + (q ? sep + "q=" + encodeURIComponent(q) : "");
  }

  function renderGrid() {
    if (currentGrid) {
      currentGrid.destroy();
      wrapper.innerHTML = "";
    }
    const baseUrl = buildServerUrl();
    const grid = new Grid({
      columns: ["Фраза", "Дата добавления", "Действия"],
      pagination: {
        limit: 100,
        server: {
          url: (prev, page, limit) => {
            const sep = prev.indexOf("?") >= 0 ? "&" : "?";
            return prev + sep + "limit=" + limit + "&offset=" + page * limit;
          },
        },
      },
      server: {
        url: baseUrl,
        then: (res) => {
          const q = searchEl?.value?.trim() ?? "";
          return (res.data || []).map((row) => [
            html(highlightSearch(row.phrase, q)),
            row.created_at,
            html(actionsHtml(row)),
          ]);
        },
        total: (res) => res.total || 0,
      },
    });
    grid.render(wrapper);
    currentGrid = grid;
  }

  if (searchEl) {
    searchEl.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(renderGrid, DEBOUNCE_MS);
    });
  }
  renderGrid();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initWordsList);
} else {
  initWordsList();
}
