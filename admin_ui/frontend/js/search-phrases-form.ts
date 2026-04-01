/**
 * Shared "add search phrase" behaviour for forms that include _search_phrases_block.html.
 * Uses delegation so it works when the form is loaded dynamically (e.g. in a modal).
 */
function initSearchPhrasesForm(): void {
  document.addEventListener("click", (e: Event) => {
    const target = e.target as HTMLElement;
    const removeBtn = target.closest(".search-phrases-remove");

    if (removeBtn) {
      e.preventDefault();
      e.stopPropagation();
      const row = removeBtn.closest(".search-phrases-row") ?? removeBtn.parentElement;
      if (row) row.remove();
      return;
    }

    const addBtn = target.closest("button.search-phrases-add");
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
    row.style.gridTemplateColumns = "120px 1fr auto";

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
    const optFullName = document.createElement("option");
    optFullName.value = "full_name";
    optFullName.textContent = "ФИО";
    select.appendChild(optText);
    select.appendChild(optSurname);
    select.appendChild(optFullName);

    const input = document.createElement("input");
    input.type = "text";
    input.name = "search_terms_text";
    input.value = value;
    input.className = "inputField inputField__default";
    input.placeholder = "Фраза";

    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.className = "btn btn__secondary search-phrases-remove";
    removeButton.setAttribute("aria-label", "Удалить");
    removeButton.textContent = "Удалить";

    row.appendChild(select);
    row.appendChild(input);
    row.appendChild(removeButton);
    listEl.appendChild(row);
  });
}

initSearchPhrasesForm();
