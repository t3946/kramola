import { setInvalidBorder } from './HighlightUploadFormView.js';

export default class HighlightUploadValidator {
  /**
   * @param {{
   *  view: import('./HighlightUploadFormView.js').default,
   *  errorPresenter: import('./ErrorPresenter.js').default,
   *  tabs: import('./InputMethodTabsController.js').default,
   * }} params
   */
  constructor({ view, errorPresenter, tabs }) {
    this.view = view;
    this.errorPresenter = errorPresenter;
    this.tabs = tabs;
  }

  /**
   * @returns {{isHighlightForm: boolean, isFootnotesForm: boolean}}
   */
  getFormType() {
    const action = this.view.uploadForm?.getAttribute('action') || '';

    return {
      isHighlightForm: action.includes('highlight.process') || action.includes('highlight.process_async'),
      isFootnotesForm: action.includes('footnotes.process'),
    };
  }

  /**
   * @returns {boolean}
   */
  validateFileExtensions() {
    if (!this.view.uploadForm) {
      return true;
    }

    const { isHighlightForm, isFootnotesForm } = this.getFormType();
    let isValid = true;

    const sourceFile = this.view.sourceFileInput?.files?.[0];
    if (sourceFile) {
      const fileName = sourceFile.name.toLowerCase();

      const allowed = isFootnotesForm ? /\.docx$/i : /\.(docx|pdf|odt)$/i;
      const errorMessage = isFootnotesForm
        ? 'Ошибка: Исходный документ должен быть в формате .docx.'
        : 'Ошибка: Исходный документ должен быть в формате .docx, .pdf или .odt.';
      const defaultInfoText = isFootnotesForm
        ? 'Файл: docx | файл не выбран'
        : 'Файл: docx, pdf, odt | файл не выбран';

      if (!allowed.test(fileName)) {
        this.errorPresenter.showClientError(`${errorMessage} Некорректный файл: ${sourceFile.name}`);
        setInvalidBorder(this.view.sourceFileButton || this.view.sourceFileInput, true);

        if (this.view.sourceFileInput) {
          this.view.sourceFileInput.value = '';
        }

        this.view.setSourceFileInfo(defaultInfoText);

        window.scrollTo(0, 0);
        isValid = false;
      } else {
        setInvalidBorder(this.view.sourceFileButton || this.view.sourceFileInput, false);
      }
    }

    const wordsFile = this.view.wordsFileInput?.files?.[0];
    if (wordsFile) {
      const fileName = wordsFile.name.toLowerCase();
      const allowed = isHighlightForm ? /\.(docx|xlsx|txt)$/i : /\.docx$/i;
      const errorMessage = isHighlightForm
        ? 'Ошибка: Файл со словами должен быть в формате .docx, .xlsx или .txt.'
        : 'Ошибка: Файл со словами должен быть в формате .docx.';
      const defaultInfoText = isHighlightForm ? 'Файл: docx, xlsx, txt | файл не выбран' : 'Файл: docx | файл не выбран';

      if (!allowed.test(fileName)) {
        this.errorPresenter.showClientError(`${errorMessage} Некорректный файл: ${wordsFile.name}`);
        setInvalidBorder(this.view.wordsFileButton || this.view.wordsFileInput, true);

        if (this.view.wordsFileInput) {
          this.view.wordsFileInput.value = '';
        }

        this.view.setWordsFileInfo(defaultInfoText);

        window.scrollTo(0, 0);
        isValid = false;
      } else {
        setInvalidBorder(this.view.wordsFileButton || this.view.wordsFileInput, false);
      }
    }

    return isValid;
  }

  /**
   * @returns {boolean}
   */
  validateFields() {
    this.view.resetHighlights();
    this.errorPresenter.clearClientError();

    if (!this.view.uploadForm || !this.view.sourceFileInput) {
      this.errorPresenter.showClientError('Ошибка конфигурации страницы. Обновите.');

      return false;
    }

    const sourceFileSelected = this.view.sourceFileInput.files.length > 0;
    const { isHighlightForm, isFootnotesForm } = this.getFormType();

    if (!isHighlightForm) {
      if (sourceFileSelected) {
        return true;
      }

      const errorText = isFootnotesForm
        ? 'Ошибка: Необходимо загрузить исходный документ (.docx).'
        : 'Ошибка: Необходимо загрузить исходный документ.';
      this.errorPresenter.showClientError(errorText);
      setInvalidBorder(this.view.sourceFileButton || this.view.sourceFileInput, true);
      window.scrollTo(0, 0);

      return false;
    }

    const wordsFileSelected = this.view.wordsFileInput ? this.view.wordsFileInput.files.length > 0 : false;
    const wordsTextEntered = this.view.wordsTextarea ? this.view.wordsTextarea.value.trim().length > 0 : false;
    const predefinedListSelected = [...this.view.predefinedCheckboxes].some((checkbox) => checkbox.checked);
    const selectedMethod = this.tabs.getSelectedMethod();

    const hasWordsSource = predefinedListSelected
      || (selectedMethod === 'file' && wordsFileSelected)
      || (selectedMethod === 'text' && wordsTextEntered);

    if (!sourceFileSelected && !hasWordsSource) {
      this.errorPresenter.showClientError(
        'Ошибка: Необходимо загрузить исходный документ (.docx, .pdf или .odt) или выбрать готовый список для поиска.'
      );
      setInvalidBorder(this.view.sourceFileButton || this.view.sourceFileInput, true);

      if (!predefinedListSelected) {
        if (selectedMethod === 'file' && !wordsFileSelected) {
          setInvalidBorder(this.view.wordsFileButton || this.view.wordsFileInput, true);
        }

        if (selectedMethod === 'text' && !wordsTextEntered) {
          setInvalidBorder(this.view.wordsTextarea, true);
        }

        setInvalidBorder(this.view.checkboxGroup, true);
      }

      window.scrollTo(0, 0);
      return false;
    }

    if (sourceFileSelected && !hasWordsSource) {
      this.errorPresenter.showClientError('Ошибка: Укажите источник слов - загрузите файл, введите текст или выберите готовый список.');

      if (selectedMethod === 'file' && !wordsFileSelected) {
        setInvalidBorder(this.view.wordsFileButton || this.view.wordsFileInput, true);
      }

      if (selectedMethod === 'text' && !wordsTextEntered) {
        setInvalidBorder(this.view.wordsTextarea, true);
      }

      setInvalidBorder(this.view.checkboxGroup, true);
      window.scrollTo(0, 0);

      return false;
    }

    return true;
  }
}

