/**
 * Shared "add search phrase" behaviour for forms that include _search_phrases_block.html.
 * Uses delegation so it works when the form is loaded dynamically (e.g. in a modal).
 */
function initSearchPhrasesForm(): void {
  document.addEventListener("click", (e: Event) => {
    const addBtn = (e.target as HTMLElement).closest("button.search-phrases-add");
    if (!addBtn) return;

    e.preventDefault();
    const block = addBtn.closest(".search-phrases-block");
    if (!block) return;

    const newInput = block.querySelector<HTMLInputElement>("input.search-phrases-new");
    const listEl = block.querySelector(".search-phrases-list");
    if (!newInput || !listEl) return;

    const value = newInput.value.trim();
    if (!value) return;

    newInput.value = "";
    const row = document.createElement("div");
    row.className = "search-phrases-row grid gap-2";
    row.style.gridTemplateColumns = "120px 1fr";

    const select = document.createElement("select");
    select.name = "search_terms_type";
    select.className = "inputField inputField__default";
    select.setAttribute("aria-label", "Тип");
    const optText = document.createElement("option");
    optText.value = "text";
    optText.textContent = "Текст";
    optText.selected = true;
    const optSurname = document.createElement("option");
    optSurname.value = "surname";
    optSurname.textContent = "Фамилия";
    select.appendChild(optText);
    select.appendChild(optSurname);

    const input = document.createElement("input");
    input.type = "text";
    input.name = "search_terms_text";
    input.value = value;
    input.className = "inputField inputField__default";
    input.placeholder = "Фраза";

    row.appendChild(select);
    row.appendChild(input);
    listEl.appendChild(row);
  });
}

initSearchPhrasesForm();
