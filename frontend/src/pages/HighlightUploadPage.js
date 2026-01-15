import socketIOService from '../services/SocketioService.js';
import BaseComponent from '../components/BaseComponent.js';
import ErrorPresenter from '../components/ErrorPresenter.js';
import InputMethodTabsController from '../components/InputMethodTabsController.js';
import HighlightUploadFormView from '../components/HighlightUploadFormView.js';
import HighlightUploadValidator from '../components/HighlightUploadValidator.js';
import HighlightPageBridge from '../components/HighlightPageBridge.js';

class HighlightUploadPage {
  constructor() {
    this.view = new HighlightUploadFormView();
    this.errorPresenter = new ErrorPresenter({
      clientErrorEl: this.view.clientErrorMessage,
      serverErrorEl: this.view.serverErrorMessage,
    });

    this.tabs = new InputMethodTabsController({
      fileInputContainer: this.view.fileInputContainer,
      textInputContainer: this.view.textInputContainer,
      fileLabel: this.view.fileLabel,
      textLabel: this.view.textLabel,
      wordsTextarea: this.view.wordsTextarea,
    });

    this.validator = new HighlightUploadValidator({
      view: this.view,
      errorPresenter: this.errorPresenter,
      tabs: this.tabs,
    });

    this.init();
  }

  /**
   * @returns {void}
   */
  init() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());

      return;
    }

    this.setup();
  }

  /**
   * @returns {void}
   */
  setup() {
    socketIOService.connect().then(() => undefined, () => undefined);
    BaseComponent.initComponents();

    if (!this.view.uploadForm) {
      return;
    }

    this.bindUiHandlers();
    this.tabs.syncView();
    this.tabs.adjustTextareaHeight();
  }

  /**
   * @returns {void}
   */
  bindUiHandlers() {
    if (this.view.sourceFileInput) {
      this.view.sourceFileInput.addEventListener('change', () => {
        this.view.resetHighlights();
        this.validator.validateFileExtensions();
        this.view.setSourceFileInfo('Файл: docx, pdf, odt | файл не выбран');
      });
    }

    if (this.view.wordsFileInput) {
      this.view.wordsFileInput.addEventListener('change', () => {
        this.view.resetHighlights();
        this.validator.validateFileExtensions();
        this.view.setWordsFileInfo('Файл: docx, xlsx, txt | файл не выбран');
      });
    }

    if (this.view.wordsTextarea) {
      this.view.wordsTextarea.addEventListener('input', () => {
        this.view.resetHighlights();
        this.tabs.adjustTextareaHeight();
      });
    }

    [...this.view.predefinedCheckboxes].forEach((checkbox) => {
      checkbox.addEventListener('change', () => this.view.resetHighlights());
    });

    [...this.view.inputMethodRadios].forEach((radio) => {
      radio.addEventListener('change', () => {
        this.view.resetHighlights();
        this.tabs.syncView();
      });
    });

    this.view.uploadForm?.addEventListener('submit', (event) => {
      event.preventDefault();
      this.handleSubmit();
    });
  }

  /**
   * @returns {void}
   */
  handleSubmit() {
    this.errorPresenter.clearClientError();

    if (this.view.serverErrorMessage?.style) {
      this.view.serverErrorMessage.style.display = 'none';
    }

    if (!this.validator.validateFields()) {
      return;
    }

    if (!this.validator.validateFileExtensions()) {
      return;
    }

    const form = this.view.uploadForm;
    if (!form) {
      return;
    }

    const formData = new FormData(form);
    this.view.setProcessingState(true);

    fetch(form.action, {
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

        this.view.setProcessingState(false);

        if (payload?.nonJsonText) {
          const textPreview = payload.nonJsonText.substring(0, 200);
          this.errorPresenter.showClientError(
            `Неожиданный ответ сервера (не JSON): ${payload.status}. Ответ: ${textPreview}...`
          );

          return;
        }

        const errorMsg = data?.error || `Ошибка сервера: ${payload?.status || 'unknown'}`;
        this.errorPresenter.showClientError(errorMsg);
      }, (error) => {
        this.view.setProcessingState(false);

        const message = error instanceof Error ? error.message : 'Unknown error';
        this.errorPresenter.showClientError(`Произошла ошибка при отправке запроса: ${message}`);
      });
  }
}

new HighlightUploadPage();

