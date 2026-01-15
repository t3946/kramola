import JustValidate from 'just-validate';

import BaseComponent from '../BaseComponent.js';
import ErrorPresenter from '../ErrorPresenter.js';
import InputMethodTabsController from '../InputMethodTabsController.js';
import HighlightPageBridge from '../HighlightPageBridge.js';
import { getFirst, setInvalidBorder } from '../HighlightUploadFormView.js';
import InputFile from '../ui/InputFile.js';

/**
 * @typedef {'file'|'text'} InputMethod
 */

export default class AnalyseForm extends BaseComponent {
  static commonClass = 'js-analyse-form';

  constructor(el) {
    super(el);

    /** @type {HTMLFormElement} */
    this.formEl = /** @type {HTMLFormElement} */ (this.el);

    /** @type {ErrorPresenter|null} */
    this.errorPresenter = null;

    /** @type {InputMethodTabsController|null} */
    this.tabs = null;

    /** @type {JustValidate|null} */
    this.validator = null;

    /** @type {HTMLButtonElement|null} */
    this.submitButtonEl = null;

    /** @type {HTMLTextAreaElement|null} */
    this.wordsTextareaEl = null;

    /** @type {HTMLElement|null} */
    this.checkboxGroupEl = null;

    /** @type {NodeListOf<HTMLInputElement>} */
    this.predefinedCheckboxes = /** @type {NodeListOf<HTMLInputElement>} */ ([]);

    /** @type {NodeListOf<HTMLInputElement>} */
    this.inputMethodRadios = /** @type {NodeListOf<HTMLInputElement>} */ ([]);

    /** @type {InputFile|null} */
    this.sourceInput = null;

    /** @type {InputFile|null} */
    this.wordsInput = null;

    this.init();
  }

  /**
   * @returns {void}
   */
  init() {
    this.submitButtonEl = /** @type {HTMLButtonElement|null} */ (this.formEl.querySelector('#submitButton'));
    this.wordsTextareaEl = /** @type {HTMLTextAreaElement|null} */ (this.formEl.querySelector('#words-textarea'));
    this.checkboxGroupEl = getFirst('.checkbox-group');
    this.predefinedCheckboxes = this.formEl.querySelectorAll('input[name="predefined_list_keys"]');
    this.inputMethodRadios = this.formEl.querySelectorAll('input[name="input-method"]');

    const doc = this.formEl.ownerDocument;
    const clientErrorEl = /** @type {HTMLElement|null} */ (doc.getElementById('clientErrorMessage'));
    const serverErrorEl = /** @type {HTMLElement|null} */ (doc.getElementById('serverErrorMessage'));
    this.errorPresenter = new ErrorPresenter({ clientErrorEl, serverErrorEl });

    this.tabs = new InputMethodTabsController({
      fileInputContainer: /** @type {HTMLElement|null} */ (this.formEl.querySelector('#file-input')),
      textInputContainer: /** @type {HTMLElement|null} */ (this.formEl.querySelector('#text-input')),
      fileLabel: /** @type {HTMLElement|null} */ (this.formEl.querySelector('label[for="file-method"]')),
      textLabel: /** @type {HTMLElement|null} */ (this.formEl.querySelector('label[for="text-method"]')),
      wordsTextarea: this.wordsTextareaEl,
    });

    this.sourceInput = this._getOrCreateInputFile('source');
    this.wordsInput = this._getOrCreateInputFile('words');

    this.tabs.syncView();
    this.tabs.adjustTextareaHeight();

    this.bindUiHandlers();
    this.setupValidator();
  }

  /**
   * @param {'source'|'words'} name
   * @returns {InputFile|null}
   */
  _getOrCreateInputFile(name) {
    const wrapper = /** @type {HTMLElement|null} */ (
      this.formEl.querySelector(`.js-input-file[data-input-name="${name}"]`)
    );

    if (!wrapper) {
      return null;
    }

    const existing = /** @type {any} */ (wrapper).instance;
    if (existing && existing instanceof InputFile) {
      return existing;
    }

    return new InputFile(wrapper);
  }

  /**
   * @returns {InputMethod}
   */
  getSelectedMethod() {
    const selected = /** @type {HTMLInputElement|null} */ (this.formEl.querySelector('input[name="input-method"]:checked'));
    const value = selected?.getAttribute('value');

    return value === 'text' ? 'text' : 'file';
  }

  /**
   * @returns {{sourceSelected: boolean, wordsFileSelected: boolean, wordsTextEntered: boolean, predefinedSelected: boolean}}
   */
  getFormState() {
    const sourceSelected = Boolean(this.sourceInput?.hasFile());
    const wordsFileSelected = Boolean(this.wordsInput?.hasFile());
    const wordsTextEntered = Boolean(this.wordsTextareaEl?.value?.trim().length);
    const predefinedSelected = [...this.predefinedCheckboxes].some((checkbox) => checkbox.checked);

    return {
      sourceSelected,
      wordsFileSelected,
      wordsTextEntered,
      predefinedSelected,
    };
  }

  /**
   * @returns {boolean}
   */
  hasWordsSource() {
    const state = this.getFormState();
    const method = this.getSelectedMethod();

    if (state.predefinedSelected) {
      return true;
    }

    if (method === 'file') {
      return state.wordsFileSelected;
    }

    return state.wordsTextEntered;
  }

  /**
   * @param {boolean} isProcessing
   * @returns {void}
   */
  setProcessingState(isProcessing) {
    if (!this.submitButtonEl) {
      return;
    }

    this.submitButtonEl.disabled = isProcessing;
    this.submitButtonEl.textContent = isProcessing ? 'Обрабатывается...' : 'Обработать';
  }

  /**
   * @returns {void}
   */
  resetHighlights() {
    this.sourceInput?.setInvalid(false);
    this.wordsInput?.setInvalid(false);

    if (this.wordsTextareaEl) {
      setInvalidBorder(this.wordsTextareaEl, false);
    }

    if (this.checkboxGroupEl) {
      setInvalidBorder(this.checkboxGroupEl, false);
    }
  }

  /**
   * @returns {void}
   */
  bindUiHandlers() {
    const clear = () => {
      this.resetHighlights();
      this.errorPresenter?.clearClientError();
    };

    if (this.sourceInput?.inputEl) {
      this.sourceInput.inputEl.addEventListener('change', clear);
    }

    if (this.wordsInput?.inputEl) {
      this.wordsInput.inputEl.addEventListener('change', clear);
    }

    if (this.wordsTextareaEl) {
      this.wordsTextareaEl.addEventListener('input', () => {
        clear();
        this.tabs?.adjustTextareaHeight();
      });
    }

    [...this.predefinedCheckboxes].forEach((checkbox) => checkbox.addEventListener('change', clear));

    [...this.inputMethodRadios].forEach((radio) => {
      radio.addEventListener('change', () => {
        clear();
        this.tabs?.syncView();
      });
    });

    this.formEl.addEventListener('submit', (event) => {
      event.preventDefault();
      this.errorPresenter?.clearClientError();

      if (!this.validator) {
        return;
      }

      this.validator.validate();
    });
  }

  /**
   * @returns {void}
   */
  setupValidator() {
    const sourceSelector = '#source_file';
    const wordsFileSelector = '#words_file';
    const wordsTextSelector = '#words-textarea';

    this.validator = new JustValidate(this.formEl, {
      focusInvalidField: false,
      errorFieldCssClass: '',
      errorLabelCssClass: 'hidden',
    });

    this.validator
      .addField(sourceSelector, [
        {
          validator: () => {
            const state = this.getFormState();

            return state.sourceSelected || this.hasWordsSource();
          },
          errorMessage: 'Ошибка: Необходимо загрузить исходный документ или выбрать источник слов для поиска.',
        },
        {
          validator: () => {
            const fileName = this.sourceInput?.getFile()?.name?.toLowerCase() || '';

            if (!fileName) {
              return true;
            }

            return this._isFileAllowed(this.sourceInput);
          },
          errorMessage: `Ошибка: Исходный документ должен быть в формате ${this._formatAllowedFormats(this.sourceInput)}.`,
        },
      ])
      .addField(wordsFileSelector, [
        {
          validator: () => {
            const state = this.getFormState();
            const method = this.getSelectedMethod();

            if (!state.sourceSelected) {
              return true;
            }

            if (state.predefinedSelected) {
              return true;
            }

            if (method !== 'file') {
              return true;
            }

            return state.wordsFileSelected;
          },
          errorMessage: 'Ошибка: Укажите источник слов — загрузите файл, введите текст или выберите готовый список.',
        },
        {
          validator: () => {
            const fileName = this.wordsInput?.getFile()?.name?.toLowerCase() || '';

            if (!fileName) {
              return true;
            }

            return this._isFileAllowed(this.wordsInput);
          },
          errorMessage: `Ошибка: Файл со словами должен быть в формате ${this._formatAllowedFormats(this.wordsInput)}.`,
        },
      ])
      .addField(wordsTextSelector, [
        {
          validator: () => {
            const state = this.getFormState();
            const method = this.getSelectedMethod();

            if (!state.sourceSelected) {
              return true;
            }

            if (state.predefinedSelected) {
              return true;
            }

            if (method !== 'text') {
              return true;
            }

            return state.wordsTextEntered;
          },
          errorMessage: 'Ошибка: Укажите источник слов — загрузите файл, введите текст или выберите готовый список.',
        },
      ])
      .onFail((fields) => this.handleFail(fields))
      .onSuccess(() => this.handleSuccess());
  }

  /**
   * @param {Record<string, {elem: Element, errors: string[], isValid: boolean}>} fields
   * @returns {void}
   */
  handleFail(fields) {
    this.setProcessingState(false);
    this.resetHighlights();

    const errors = Object.values(fields)
      .flatMap((field) => field.errors || [])
      .filter((msg) => Boolean(msg));

    const message = errors[0] || 'Ошибка: Проверьте корректность заполнения формы.';
    this.errorPresenter?.showClientError(message);

    const state = this.getFormState();

    if (!state.sourceSelected && !this.hasWordsSource()) {
      this.sourceInput?.setInvalid(true);
      setInvalidBorder(this.checkboxGroupEl, true);

      window.scrollTo(0, 0);
      return;
    }

    if (state.sourceSelected && !this.hasWordsSource()) {
      setInvalidBorder(this.checkboxGroupEl, true);

      if (this.getSelectedMethod() === 'file') {
        this.wordsInput?.setInvalid(true);
      } else {
        setInvalidBorder(this.wordsTextareaEl, true);
      }

      window.scrollTo(0, 0);
      return;
    }

    if (!this._isFileAllowed(this.sourceInput)) {
      this.sourceInput?.setInvalid(true);
    }

    if (!this._isFileAllowed(this.wordsInput)) {
      this.wordsInput?.setInvalid(true);
    }

    window.scrollTo(0, 0);
  }

  /**
   * @param {InputFile|null} input
   * @returns {string}
   */
  _formatAllowedFormats(input) {
    const formats = input?.getAllowedFormats() || [];

    if (!formats.length) {
      return '...';
    }

    return formats.join(', ');
  }

  /**
   * @param {InputFile|null} input
   * @returns {boolean}
   */
  _isFileAllowed(input) {
    const fileName = input?.getFile()?.name?.toLowerCase() || '';

    if (!fileName) {
      return true;
    }

    const formats = input?.getAllowedFormats() || [];

    if (!formats.length) {
      return true;
    }

    return formats.some((ext) => fileName.endsWith(ext));
  }

  /**
   * @returns {void}
   */
  handleSuccess() {
    const formData = new FormData(this.formEl);
    this.setProcessingState(true);

    fetch(this.formEl.action, {
      method: 'POST',
      body: formData,
    })
      .then((response) => {
        const contentType = response.headers.get('content-type') || '';

        if (!contentType.includes('application/json')) {
          return response.text().then((text) => ({
            ok: false,
            status: response.status,
            data: null,
            nonJsonText: text,
          }));
        }

        return response.json().then((data) => ({
          ok: response.ok,
          status: response.status,
          data,
          nonJsonText: null,
        }));
      }, (error) => Promise.reject(error))
      .then((payload) => {
        /** @type {{task_id?: string, error?: string}|null} */
        const data = payload?.data || null;

        if (payload?.ok && data?.task_id) {
          HighlightPageBridge.sendTaskId(data.task_id);

          return;
        }

        this.setProcessingState(false);

        if (payload?.nonJsonText) {
          const textPreview = payload.nonJsonText.substring(0, 200);
          this.errorPresenter?.showClientError(
            `Неожиданный ответ сервера (не JSON): ${payload.status}. Ответ: ${textPreview}...`
          );

          return;
        }

        const errorMsg = data?.error || `Ошибка сервера: ${payload?.status || 'unknown'}`;
        this.errorPresenter?.showClientError(errorMsg);
      }, (error) => {
        this.setProcessingState(false);

        const message = error instanceof Error ? error.message : 'Unknown error';
        this.errorPresenter?.showClientError(`Произошла ошибка при отправке запроса: ${message}`);
      });
  }
}

AnalyseForm.register();

