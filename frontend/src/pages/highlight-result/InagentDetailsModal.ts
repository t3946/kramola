/**
 * Inagent details modal: loads and shows fragment by phrase
 */
import u from 'umbrellajs';

const MODAL_CLASS = 'inagent-details-modal';
const MODAL_BODY_CLASS = 'inagent-details-modal__body';

export class InagentDetailsModal {
    private readonly detailsUrl: string;
    private readonly modal: Element | null;
    private readonly modalBody: Element | null;

    constructor(detailsUrl: string) {
        this.detailsUrl = detailsUrl;
        this.modal = document.querySelector(`.${MODAL_CLASS}`);
        this.modalBody = document.querySelector(`.${MODAL_BODY_CLASS}`);
        this._bindClose();
    }

    show(phrase: string): Promise<void> {
        if (!this.modal || !this.modalBody) return Promise.resolve();
        (this.modalBody as HTMLElement).innerHTML = '<p class="text-gray-500">Загрузка…</p>';
        this.modal.classList.remove('hidden');
        const url = `${this.detailsUrl}?phrase=${encodeURIComponent(phrase)}`;
        return fetch(url, {headers: {Accept: 'text/html'}})
            .then((r) => r.text())
            .then((html) => {
                (this.modalBody as HTMLElement).innerHTML = html;
            });
    }

    private _bindClose(): void {
        const $pageEl = u('.highlightResultPage');
        $pageEl.on('click', '[data-modal-close]', (e) => {
            const target = (e.target as HTMLElement).closest('[data-modal-close]');
            if (target) {
                const modalClass = target.getAttribute('data-modal-close');
                if (modalClass) document.querySelector(`.${modalClass}`)?.classList.add('hidden');
            }
        });
    }
}
