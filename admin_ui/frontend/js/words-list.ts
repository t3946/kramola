import { Grid, html } from "gridjs";

const DEBOUNCE_MS = 300;

interface WordsRow {
  phrase: string;
  edit_url: string;
  delete_url: string;
  created_at: string;
}

interface WordsApiResponse {
  data?: WordsRow[];
  total?: number;
}

function escapeHtml(s: string): string {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

function highlightSearch(text: string, searchTerm: string): string {
  if (!searchTerm) return escapeHtml(text);
  const escapedSearch = searchTerm.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const re = new RegExp("(" + escapedSearch + ")", "gi");
  const parts = text.split(re);
  return parts
    .map((part: string, i: number) =>
      i % 2 === 1
        ? '<span class="search-highlight">' + escapeHtml(part) + "</span>"
        : escapeHtml(part)
    )
    .join("");
}

function actionsHtml(row: WordsRow): string {
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

function initWordsList(): void {
  document.querySelectorAll("[data-modal-open]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-modal-open");
      if (id) document.getElementById(id)?.classList.remove("hidden");
    });
  });
  document.querySelectorAll("[data-modal-close]").forEach((el) => {
    el.addEventListener("click", () => {
      const id = el.getAttribute("data-modal-close");
      if (id) document.getElementById(id)?.classList.add("hidden");
    });
  });

  const wrapper = document.getElementById("words-grid-wrapper");
  const searchEl = document.getElementById("word-search") as HTMLInputElement | null;
  const dataUrl = searchEl?.getAttribute("data-data-url") ?? null;
  if (!dataUrl || !wrapper) return;
  const dataUrlStr: string = dataUrl;
  const wrapperEl: HTMLElement = wrapper;

  let debounceTimer: ReturnType<typeof setTimeout> | null = null;
  let currentGrid: Grid | null = null;

  wrapperEl.addEventListener("click", (e: Event) => {
    const target = e.target as HTMLElement;
    const editBtn = target.closest("button[data-edit-url]");
    if (editBtn) {
      const form = document.getElementById("edit-phrase-form");
      const input = document.getElementById("edit-phrase-input");
      if (form && input) {
        (form as HTMLFormElement).action = editBtn.getAttribute("data-edit-url") ?? "";
        (input as HTMLInputElement).value = editBtn.getAttribute("data-phrase") ?? "";
        document.getElementById("edit-phrase-modal")?.classList.remove("hidden");
      }
      return;
    }
    const delBtn = target.closest("button[data-delete-url]");
    if (delBtn) {
      const form = document.getElementById("delete-phrase-form");
      const message = document.getElementById("delete-phrase-message");
      if (form && message) {
        (form as HTMLFormElement).action = delBtn.getAttribute("data-delete-url") ?? "";
        message.textContent =
          "Удалить фразу «" + (delBtn.getAttribute("data-phrase") ?? "") + "» из списка?";
        document.getElementById("delete-phrase-modal")?.classList.remove("hidden");
      }
    }
  });

  function buildServerUrl(): string {
    const q = searchEl?.value.trim();
    const sep = dataUrlStr.indexOf("?") >= 0 ? "&" : "?";
    return dataUrlStr + (q ? sep + "q=" + encodeURIComponent(q) : "");
  }

  function renderGrid(): void {
    if (currentGrid) {
      currentGrid.destroy();
      wrapperEl.innerHTML = "";
    }
    const baseUrl = buildServerUrl();
    const grid = new Grid({
      columns: ["Фраза", "Дата добавления", "Действия"],
      pagination: {
        limit: 100,
        server: {
          url: (prev: string, page: number, limit: number) => {
            const sep = prev.indexOf("?") >= 0 ? "&" : "?";
            return prev + sep + "limit=" + limit + "&offset=" + page * limit;
          },
        },
      },
      server: {
        url: baseUrl,
        then: (res: WordsApiResponse) => {
          const q = searchEl?.value?.trim() ?? "";
          return (res.data ?? []).map((row: WordsRow) => [
            html(highlightSearch(row.phrase, q)),
            row.created_at,
            html(actionsHtml(row)),
          ]);
        },
        total: (res: WordsApiResponse) => res.total ?? 0,
      },
    });
    grid.render(wrapperEl);
    currentGrid = grid;
  }

  if (searchEl) {
    searchEl.addEventListener("input", () => {
      if (debounceTimer) clearTimeout(debounceTimer);
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
