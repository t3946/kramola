import socketIOService from './services/SocketioService.js';
import BaseComponent from './components/BaseComponent.js';
import {onDocumentReady} from './utils/onDocumentReady.js';

import {Highlight} from './pages/Highlight.js';
import {HighlightResult} from './pages/highlight-result/HighlightResult.js';

/**
 * @returns {void}
 */

onDocumentReady(() => {
    if (window.app) {
        return
    }

    const app = {
        pages: {
            highlight: new Highlight(),
            highlightResult: new HighlightResult(),
        }
    }

    socketIOService.connect().then(() => undefined, () => undefined);
    BaseComponent.initComponents();
    window.app = app
});
