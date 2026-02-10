import { Grid, html } from "gridjs";

const DEBOUNCE_MS = 300;

interface InagentsRow {
  id: number;
  registry_number: number | null;
  full_name: string;
  status_label: string;
  agent_type: string;
  agent_type_label: string;
  edit_form_url: string;
  edit_save_url: string;
}

interface InagentsApiResponse {
  data?: InagentsRow[];
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

function editButtonHtml(row: InagentsRow): string {
  return (
    '<button type="button" class="btn btn-sm btn-outline-primary gridjs-btn" title="Изменить" data-edit-form-url="' +
    escapeHtml(row.edit_form_url) +
    '"><i class="fa fa-pencil"></i></button>'
  );
}

function initInagentsList(): void {
  const wrapper = document.getElementById("inagents-grid-wrapper");
  const searchEl = document.getElementById("inagent-search") as HTMLInputElement | null;
  const typeFilterEl = document.getElementById("inagent-type-filter") as HTMLSelectElement | null;
  const dataUrl = searchEl?.getAttribute("data-data-url") ?? null;
  if (!dataUrl || !wrapper) return;

  const dataUrlStr: string = dataUrl;
  const wrapperEl: HTMLElement = wrapper;
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;
  let currentGrid: Grid | null = null;

  document.querySelectorAll("[data-modal-close]").forEach((el) => {
    el.addEventListener("click", () => {
      const id = el.getAttribute("data-modal-close");
      if (id) document.getElementById(id)?.classList.add("hidden");
    });
  });
  document.getElementById("inagent-edit-modal")?.querySelector(".fixed.inset-0.bg-black")?.addEventListener("click", () => {
    document.getElementById("inagent-edit-modal")?.classList.add("hidden");
  });

  const modalBody = document.getElementById("inagent-edit-modal-body");
  const modal = document.getElementById("inagent-edit-modal");

  wrapperEl.addEventListener("click", (e: Event) => {
    const target = e.target as HTMLElement;
    const editBtn = target.closest("button[data-edit-form-url]");
    if (editBtn && modalBody && modal) {
      const url = editBtn.getAttribute("data-edit-form-url") ?? "";
      modalBody.innerHTML = "<p class=\"text-gray-500\">Загрузка…</p>";
      modal.classList.remove("hidden");
      fetch(url, { headers: { Accept: "text/html" } })
        .then((r) => r.text())
        .then((html) => {
          modalBody.innerHTML = html;
        })
        .catch(() => {
          modalBody.innerHTML = "<p class=\"text-red-600\">Ошибка загрузки формы.</p>";
        });
    }
  });

  modal?.addEventListener("submit", (e: Event) => {
    const form = (e.target as HTMLElement).closest("form.inagent-edit-form");
    if (!form || !(form instanceof HTMLFormElement)) return;
    e.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn instanceof HTMLButtonElement) submitBtn.disabled = true;
    const formData = new FormData(form);
    const saveUrl = form.action;
    fetch(saveUrl, {
      method: "POST",
      body: formData,
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
      .then((r) => r.json())
      .then((data) => {
        if (data?.success && modal) {
          modal.classList.add("hidden");
          renderGrid();
        }
      })
      .finally(() => {
        if (submitBtn instanceof HTMLButtonElement) submitBtn.disabled = false;
      });
  });

  function buildServerUrl(): string {
    const q = searchEl?.value.trim() ?? "";
    const agentType = typeFilterEl?.value ?? "";
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (agentType) params.set("agent_type", agentType);
    const sep = dataUrlStr.indexOf("?") >= 0 ? "&" : "?";
    return dataUrlStr + (params.toString() ? sep + params.toString() : "");
  }

  function renderGrid(): void {
    if (currentGrid) {
      currentGrid.destroy();
      wrapperEl.innerHTML = "";
    }
    const baseUrl = buildServerUrl();
    const grid = new Grid({
      columns: ["№ п/п", "Полное наименование / ФИО", "Статус инагента", "Тип", "Действия"],
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
        then: (res: InagentsApiResponse) => {
          const q = searchEl?.value?.trim() ?? "";
          return (res.data ?? []).map((row: InagentsRow) => [
            row.registry_number ?? "",
            html(highlightSearch(row.full_name, q)),
            row.status_label,
            row.agent_type_label,
            html(editButtonHtml(row)),
          ]);
        },
        total: (res: InagentsApiResponse) => res.total ?? 0,
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
  if (typeFilterEl) {
    typeFilterEl.addEventListener("change", renderGrid);
  }
  renderGrid();
}

function init(): void {
  if (document.getElementById("inagents-grid-wrapper")) {
    initInagentsList();
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
