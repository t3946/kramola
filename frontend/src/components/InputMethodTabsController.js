/**
 * @typedef {'file'|'text'} InputMethod
 */

/**
 * @typedef {{
 *  fileInputContainer: HTMLElement|null,
 *  textInputContainer: HTMLElement|null,
 *  fileLabel: HTMLElement|null,
 *  textLabel: HTMLElement|null,
 *  wordsTextarea: HTMLTextAreaElement|null,
 * }} InputMethodTabsControllerParams
 */

export default class InputMethodTabsController {
  /**
   * @param {InputMethodTabsControllerParams} params
   */
  constructor({ fileInputContainer, textInputContainer, fileLabel, textLabel, wordsTextarea }) {
    /** @type {HTMLElement|null} */
    this.fileInputContainer = fileInputContainer;

    /** @type {HTMLElement|null} */
    this.textInputContainer = textInputContainer;

    /** @type {HTMLElement|null} */
    this.fileLabel = fileLabel;

    /** @type {HTMLElement|null} */
    this.textLabel = textLabel;

    /** @type {HTMLTextAreaElement|null} */
    this.wordsTextarea = wordsTextarea;
  }

  /**
   * @returns {InputMethod}
   */
  getSelectedMethod() {
    const selected = document.querySelector('input[name="input-method"]:checked');
    const value = selected?.getAttribute('value');

    return value === 'text' ? 'text' : 'file';
  }

  /**
   * @returns {void}
   */
  adjustTextareaHeight() {
    if (!this.wordsTextarea?.style) {
      return;
    }

    this.wordsTextarea.style.height = 'auto';
    this.wordsTextarea.style.height = `${Math.min(this.wordsTextarea.scrollHeight, 200)}px`;
  }

  /**
   * @returns {void}
   */
  syncView() {
    if (!this.fileInputContainer || !this.textInputContainer || !this.fileLabel || !this.textLabel) {
      return;
    }

    const method = this.getSelectedMethod();

    if (method === 'file') {
      this.fileInputContainer.classList.remove('hidden');
      this.textInputContainer.classList.add('hidden');
      this.fileLabel.classList.add('active');
      this.textLabel.classList.remove('active');

      return;
    }

    this.fileInputContainer.classList.add('hidden');
    this.textInputContainer.classList.remove('hidden');
    this.fileLabel.classList.remove('active');
    this.textLabel.classList.add('active');

    this.adjustTextareaHeight();
  }
}

