/**
 * Highlight page
 * Manages progress bar on word highlighting page
 */
import {Page} from './Page.js';
import u from 'umbrellajs';

export class HighlightResult extends Page {
    constructor() {
        super();

        const $pageEl = u('.highlightResultPage')

        $pageEl
            .find('.showInagentDetails')
            .on('click', (e) => {
                e.preventDefault()

                console.log(e.target.dataset.phrase)
            })
    }
}
