/**
 * Shared "add search phrase" behaviour for forms that include _search_phrases_block.html.
 * Uses delegation so it works when the form is loaded dynamically (e.g. in a modal).
 */
function initSearchPhrasesForm(): void {
  document.addEventListener("click", (e: Event) => {
    const addBtn = (e.target as HTMLElement).closest(".search-phrases-add");
    if (!addBtn) return;

    const block = addBtn.closest(".search-phrases-block");
    if (!block) return;

    const newInput = block.querySelector<HTMLInputElement>(".search-phrases-new");
    const listEl = block.querySelector(".search-phrases-list");
    if (!newInput || !listEl) return;

    const value = newInput.value.trim();
    if (!value) return;

    newInput.value = "";
    const div = document.createElement("div");
    const input = document.createElement("input");
    input.type = "text";
    input.name = "search_terms";
    input.value = value;
    input.className = "inputField inputField__default w-full";
    input.placeholder = "Фраза";
    div.appendChild(input);
    listEl.appendChild(div);
  });
}

initSearchPhrasesForm();
