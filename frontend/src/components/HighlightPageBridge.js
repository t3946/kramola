export default class HighlightPageBridge {
  /**
   * @param {string} taskId
   * @returns {void}
   */
  static sendTaskId(taskId) {
    if (!taskId) {
      return;
    }

    const maxAttempts = 10;
    const attemptDelayMs = 100;

    const run = (attempt) => {
      const highlightInstance = document.app?.highlightPageInstance;
      const canSend = typeof highlightInstance?.setTaskId === 'function';

      if (canSend) {
        highlightInstance.setTaskId(taskId);

        return;
      }

      if (attempt >= maxAttempts) {
        return;
      }

      setTimeout(() => run(attempt + 1), attemptDelayMs);
    };

    run(0);
  }
}

