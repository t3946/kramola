/**
 * Highlight results page
 */
import {Page} from '../Page.js';
import u from 'umbrellajs';
import {InagentDetailsModal} from './InagentDetailsModal.js';

export class HighlightResult extends Page {
    constructor() {
        super();

        const $pageEl = u('.highlightResultPage');
        const detailsUrl: string = $pageEl.attr('data-inagent-details-url') ?? '';
        const inagentModal = new InagentDetailsModal(detailsUrl);

        $pageEl.find('.showInagentDetails').on('click', (e) => {
            e.preventDefault();

            //@ts-ignore
            inagentModal.show(e.target.dataset.phrase)
        })
    }
}
