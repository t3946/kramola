/**
 * Highlight page
 * Manages progress bar on word highlighting page
 */
import {Page} from './Page.js';
import socketIOService from '../services/SocketIOService.js';
import u from 'umbrellajs';

export class Highlight extends Page {
    constructor() {
        super();

        const $pageEl = u('.js-page-highlight');
        if (!$pageEl.length) {
            return;
        }

        this.$el = $pageEl;
        this.el = $pageEl.nodes[0];
        this.progressBarInstance = null;
        this.state = {progress: 0};
        this.taskId = null;
        this.isConnectedToRoom = false;
        this.currentTaskStatus = null;
        this.statusMessage = null;
        /** Sub-step label from socket progress.phase_description (e.g. particle description) */
        this.phaseDescription = null;
        /** Last PROCESSING status text from task_status (base label before " – …") */
        this.processingBaseLabel = null;

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
            this.showTaskProgress();
        } else {
            this.hideTaskProgress();
        }

        this.updateView();
        this.updateStatusView();
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
        this.showTaskProgress();

        await socketIOService.joinTaskProgress(
            this.taskId,
            (data) => {
                this.state.progress = data.progress || 0;

                if (data.phase_description) {
                    this.phaseDescription = data.phase_description;

                    if (!this.processingBaseLabel) {
                        this.processingBaseLabel =
                            this.statusMessage || 'Обработка документа...';
                    }

                    if (!this.currentTaskStatus) {
                        this.currentTaskStatus = 'PROCESSING';
                    }
                }

                this.updateView();
                this.updateStatusView();
            },
            null,
            (data) => {
                const stateChanged: boolean = data.state !== this.currentTaskStatus;

                if (stateChanged) {
                    const oldStatus: string | null = this.currentTaskStatus;
                    this.currentTaskStatus = data.state;
                    this.statusMessage = data.status;

                    if (data.state === 'PROCESSING') {
                        this.processingBaseLabel =
                            data.status ||
                            this.processingBaseLabel ||
                            'Обработка документа...';

                        if (oldStatus != null && oldStatus !== 'PROCESSING') {
                            this.phaseDescription = null;
                        }
                    } else {
                        this.phaseDescription = null;
                    }

                    console.log(`Task status changed: ${oldStatus || 'null'} -> ${data.state}`, {
                        taskId: this.taskId,
                        status: data.status,
                        state: data.state
                    });

                    this.updateStatusView();

                    if (
                        data.state === 'COMPLETED' &&
                        !data.status?.toLowerCase().includes('ошибка') &&
                        !data.status?.toLowerCase().includes('error')
                    ) {
                        this.redirectToResults();
                    }

                    return;
                }

                this.statusMessage = data.status;

                if (data.state === 'PROCESSING') {
                    this.processingBaseLabel =
                        data.status ||
                        this.processingBaseLabel ||
                        'Обработка документа...';
                }

                this.updateStatusView();
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
            this.hideTaskProgress();
        }

        this.taskId = taskId;

        if (!this.progressBarInstance) {
            this.setup();
        }

        if (this.taskId) {
            await this.connectToProgressRoom();
        }
    }

    /**
     * Обновляет отображение статуса задачи в HTML
     * @returns {void}
     */
    updateStatusView() {
        const $statusEl = u('.js-task-status');

        if (!$statusEl.length) {
            return;
        }

        const stateUpper: string = (this.currentTaskStatus || '').toUpperCase();
        const isTerminal: boolean =
            stateUpper === 'COMPLETED' ||
            stateUpper === 'FAILED' ||
            stateUpper === 'ERROR';
        const showPhaseDetail: boolean =
            Boolean(this.phaseDescription) && !isTerminal;

        if (this.currentTaskStatus || showPhaseDetail) {
            let statusText: string =
                this.statusMessage || this.currentTaskStatus || 'Ожидание...';

            const isProcessingLike: boolean =
                stateUpper === 'PROCESSING' ||
                stateUpper === 'PENDING' ||
                showPhaseDetail;

            if (showPhaseDetail && isProcessingLike) {
                const baseRaw: string =
                    this.processingBaseLabel ||
                    this.statusMessage ||
                    'Обработка документа...';
                const base: string =
                    baseRaw.replace(/\s*\.\.\.\s*$/, '').trim() || baseRaw.trim();
                statusText = `${base} – ${this.phaseDescription}`;
            }

            $statusEl.text(statusText);
            $statusEl.attr(
                'data-state',
                this.currentTaskStatus || (showPhaseDetail ? 'PROCESSING' : '')
            );
        } else {
            $statusEl.text('Ожидание...');
            $statusEl.attr('data-state', '');
        }
    }

    /**
     * Перенаправляет на страницу результатов
     * @returns {void}
     */
    redirectToResults() {
        if (!this.taskId) {
            return;
        }

        const resultsUrl = `/highlight/results?task_id=${this.taskId}`;
        window.location.href = resultsUrl;
    }

    /**
     * Показывает блок прогресса задачи
     * @returns {void}
     */
    showTaskProgress() {
        const $container = u('.js-task-progress-container');
        if ($container.length && $container.nodes[0]) {
            $container.nodes[0].style.display = 'block';
        }
    }

    /**
     * Скрывает блок прогресса задачи
     * @returns {void}
     */
    hideTaskProgress() {
        const $container = u('.js-task-progress-container');
        if ($container.length && $container.nodes[0]) {
            $container.nodes[0].style.display = 'none';
        }
    }
}
