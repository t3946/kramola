/**
 * @param {string} id
 * @returns {HTMLElement|null}
 */
export function getById(id) {
    return document.getElementById(id);
}

/**
 * @param {Element|null} el
 * @param {boolean} isInvalid
 * @returns {void}
 */
export function setInvalidBorder(el, isInvalid) {
    if (!el || !(el instanceof HTMLElement) || !el.style) {
        return;
    }

    el.style.border = isInvalid ? '2px solid red' : '';
}

/**
 * @param {string} selector
 * @returns {HTMLElement|null}
 */
export function getFirst(selector) {
    const el = document.querySelector(selector);

    if (!el || !(el instanceof HTMLElement)) {
        return null;
    }

    return el;
}

export default class HighlightUploadFormView {
    constructor() {
        /** @type {HTMLFormElement|null} */
        this.uploadForm = /** @type {HTMLFormElement|null} */ (getById('uploadForm'));

        /** @type {HTMLButtonElement|null} */
        this.submitButton = /** @type {HTMLButtonElement|null} */ (getById('submitButton'));

        /** @type {HTMLElement|null} */
        this.clientErrorMessage = getById('clientErrorMessage');

        /** @type {HTMLElement|null} */
        this.serverErrorMessage = getById('serverErrorMessage');

        /** @type {HTMLInputElement|null} */
        this.sourceFileInput = /** @type {HTMLInputElement|null} */ (getById('source_file'));

        /** @type {HTMLInputElement|null} */
        this.wordsFileInput = /** @type {HTMLInputElement|null} */ (getById('words_file'));

        /** @type {HTMLTextAreaElement|null} */
        this.wordsTextarea = /** @type {HTMLTextAreaElement|null} */ (getById('words-textarea'));

        /** @type {NodeListOf<HTMLInputElement>} */
        this.predefinedCheckboxes = document.querySelectorAll('input[name="predefined_list_keys"]');

        /** @type {HTMLElement|null} */
        this.checkboxGroup = getFirst('.checkbox-group');

        /** @type {NodeListOf<HTMLInputElement>} */
        this.inputMethodRadios = document.querySelectorAll('input[name="input-method"]');

        /** @type {HTMLElement|null} */
        this.sourceFileButton = getFirst('button[onclick*="source_file"]');

        /** @type {HTMLElement|null} */
        this.wordsFileButton = getFirst('button[onclick*="words_file"]');

        /** @type {HTMLElement|null} */
        this.sourceFileInfo = getById('source_file_info');

        /** @type {HTMLElement|null} */
        this.wordsFileInfo = getById('words_file_info');

        /** @type {HTMLElement|null} */
        this.fileInputContainer = getById('file-input');

        /** @type {HTMLElement|null} */
        this.textInputContainer = getById('text-input');

        /** @type {HTMLElement|null} */
        this.fileLabel = getFirst('label[for="file-method"]');

        /** @type {HTMLElement|null} */
        this.textLabel = getFirst('label[for="text-method"]');
    }

    /**
     * @param {boolean} isProcessing
     * @returns {void}
     */
    setProcessingState(isProcessing) {
        if (!this.submitButton) {
            return;
        }

        this.submitButton.disabled = isProcessing;
        this.submitButton.textContent = isProcessing ? 'Обрабатывается...' : 'Обработать';
    }

    /**
     * @returns {void}
     */
    resetHighlights() {
        setInvalidBorder(this.sourceFileInput, false);
        setInvalidBorder(this.sourceFileButton, false);
        setInvalidBorder(this.wordsFileInput, false);
        setInvalidBorder(this.wordsFileButton, false);
        setInvalidBorder(this.wordsTextarea, false);
        setInvalidBorder(this.checkboxGroup, false);
    }

    /**
     * @param {string} defaultText
     * @returns {void}
     */
    setSourceFileInfo(defaultText) {
        if (!this.sourceFileInfo) {
            return;
        }

        const fileName = this.sourceFileInput?.files?.[0]?.name;
        this.sourceFileInfo.textContent = fileName ? `Файл: ${fileName}` : defaultText;
    }

    /**
     * @param {string} defaultText
     * @returns {void}
     */
    setWordsFileInfo(defaultText) {
        if (!this.wordsFileInfo) {
            return;
        }

        const fileName = this.wordsFileInput?.files?.[0]?.name;
        this.wordsFileInfo.textContent = fileName ? `Файл: ${fileName}` : defaultText;
    }
}

