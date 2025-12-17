/**
 * Highlight page
 * Manages progress bar on word highlighting page
 */
import { Page } from './Page.js';
import socketIOService from '../services/SocketIOService.js';
import u from 'umbrellajs';

class Highlight extends Page {
  constructor() {
    super();
    
    const $pageEl = u('.js-page-highlight');
    if (!$pageEl.length) {
      return;
    }
    
    this.$el = $pageEl;
    this.el = $pageEl.nodes[0];
    this.progressBarInstance = null;
    this.state = { progress: 0 };
    this.taskId = null;
    this.isConnectedToRoom = false;
    
    if (!document.app) {
      document.app = {};
    }
    document.app.highlightPageInstance = this;
    
    this.init();
  }
  
  init() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());
    } else {
      this.setup();
    }
  }
  
  setup() {
    this.findProgressBar();
    
    if (!this.taskId) {
      const urlParams = new URLSearchParams(window.location.search);
      this.taskId = urlParams.get('task_id') || urlParams.get('check_task_id');
    }
    
    if (this.taskId) {
      this.connectToProgressRoom();
    }
    
    this.updateView();
  }
  
  findProgressBar() {
    if (this.progressBarInstance) {
      return;
    }
    
    const $progressBar = u('.js-progress-bar');
    if ($progressBar.length) {
      const progressBarEl = $progressBar.nodes[0];
      if (progressBarEl?.instance) {
        this.progressBarInstance = progressBarEl.instance;
      }
    }
  }
  
  /**
   * @returns {Promise<void>}
   */
  async connectToProgressRoom() {
    if (!this.taskId || this.isConnectedToRoom) {
      return;
    }
    
    this.isConnectedToRoom = true;
    
    await socketIOService.joinTaskProgress(
      this.taskId,
      (data) => {
        this.state.progress = data.progress || 0;
        this.updateView();
      }
    );
  }
  
  updateView() {
    if (!this.progressBarInstance) {
      return;
    }
    
    this.progressBarInstance.setValue(this.state.progress || 0);
  }
  
  /**
   * @param {string} taskId
   * @returns {Promise<void>}
   */
  async setTaskId(taskId) {
    if (!taskId) {
      return;
    }
    
    if (this.taskId === taskId && this.isConnectedToRoom) {
      return;
    }
    
    if (this.taskId !== taskId) {
      this.isConnectedToRoom = false;
    }
    
    this.taskId = taskId;
    
    if (!this.progressBarInstance) {
      this.setup();
    }
    
    await this.connectToProgressRoom();
  }
}

new Highlight();
