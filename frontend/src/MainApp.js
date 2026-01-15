import socketIOService from './services/SocketioService.js';
import BaseComponent from './components/BaseComponent.js';

/**
 * @returns {void}
 */
function initMainApp() {
  socketIOService.connect().then(() => undefined, () => undefined);
  BaseComponent.initComponents();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initMainApp);
} else {
  initMainApp();
}
