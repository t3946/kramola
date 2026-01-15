/**
 * @typedef {{
 *  clientErrorEl: HTMLElement|null,
 *  serverErrorEl: HTMLElement|null,
 * }} ErrorPresenterParams
 */

export default class ErrorPresenter {
  /**
   * @param {ErrorPresenterParams} params
   */
  constructor({ clientErrorEl, serverErrorEl }) {
    /** @type {HTMLElement|null} */
    this.clientErrorEl = clientErrorEl;

    /** @type {HTMLElement|null} */
    this.serverErrorEl = serverErrorEl;
  }

  /**
   * @param {string} message
   * @returns {void}
   */
  showClientError(message) {
    if (this.serverErrorEl?.style) {
      this.serverErrorEl.style.display = 'none';
    }

    if (!this.clientErrorEl?.style) {
      return;
    }

    this.clientErrorEl.textContent = message;
    this.clientErrorEl.style.display = 'block';
  }

  /**
   * @returns {void}
   */
  clearClientError() {
    if (!this.clientErrorEl?.style) {
      return;
    }

    this.clientErrorEl.textContent = '';
    this.clientErrorEl.style.display = 'none';
  }
}

