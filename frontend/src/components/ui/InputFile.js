import BaseComponent from '../BaseComponent.js';
import { setInvalidBorder } from '../HighlightUploadFormView.js';

/**
 * UI component for a hidden <input type="file"> with a button and info label.
 */
export default class InputFile extends BaseComponent {
  static commonClass = 'js-input-file';

  constructor(el) {
    super(el);

    /** @type {HTMLInputElement|null} */
    this.inputEl = null;

    /** @type {HTMLButtonElement|null} */
    this.buttonEl = null;

    /** @type {HTMLElement|null} */
    this.infoEl = null;

    /** @type {string} */
    this.defaultInfoText = '';

    this.init();
  }

  /**
   * @returns {void}
   */
  init() {
    this.inputEl = /** @type {HTMLInputElement|null} */ (this.el.querySelector('input[type="file"]'));
    this.buttonEl = /** @type {HTMLButtonElement|null} */ (this.el.querySelector('button[type="button"]'));
    this.infoEl = /** @type {HTMLElement|null} */ (this.el.querySelector('.file-info'));
    this.defaultInfoText = (this.infoEl?.textContent || '').trim();

    if (this.buttonEl) {
      this.buttonEl.addEventListener('click', (event) => {
        event.preventDefault();

        if (this.inputEl) {
          this.inputEl.click();
        }
      });
    }

    if (this.inputEl) {
      this.inputEl.addEventListener('change', () => this.updateView());
    }

    this.updateView();
  }

  /**
   * @returns {File|null}
   */
  getFile() {
    const file = this.inputEl?.files?.[0];

    return file || null;
  }

  /**
   * @returns {boolean}
   */
  hasFile() {
    return Boolean(this.getFile());
  }

  /**
   * Returns allowed file extensions parsed from input's accept attribute.
   * Example: accept=".docx,.xlsx,.txt" -> ['.docx', '.xlsx', '.txt']
   *
   * @returns {string[]}
   */
  getAllowedFormats() {
    const acceptRaw = this.inputEl?.getAttribute('accept') || '';

    if (!acceptRaw.trim()) {
      return [];
    }

    return acceptRaw
      .split(',')
      .map((part) => part.trim().toLowerCase())
      .filter((part) => part.startsWith('.') && part.length > 1);
  }

  /**
   * @param {boolean} isInvalid
   * @returns {void}
   */
  setInvalid(isInvalid) {
    setInvalidBorder(this.buttonEl, isInvalid);

    if (this.inputEl) {
      setInvalidBorder(this.inputEl, isInvalid);
    }
  }

  /**
   * @returns {void}
   */
  clear() {
    if (!this.inputEl) {
      return;
    }

    this.inputEl.value = '';
    this.updateView();
  }

  updateView() {
    if (!this.infoEl) {
      return;
    }

    const fileName = this.getFile()?.name;
    this.infoEl.textContent = fileName ? `Файл: ${fileName}` : this.defaultInfoText;
  }
}

InputFile.register();

