/**
 * Скрипт для страницы highlight
 * Управляет прогресс-баром на странице выделения слов
 */

import { Page } from './Page.js';
import socketIOService from '../services/SocketIOService.js';
import u from 'umbrellajs';

class Highlight extends Page {
    constructor() {
        super();
        
        // Ищем страницу по CSS классу
        const $pageEl = u('.js-page-highlight');
        if (!$pageEl.length) {
            return;
        }
        
        // Сохраняем элемент страницы
        this.$el = $pageEl;
        this.el = $pageEl.nodes[0];
        
        // Ищем прогресс-бар по CSS классу и получаем его instance
        const $progressBar = u('.js-progress-bar');
        if ($progressBar.length) {
            const progressBarEl = $progressBar.nodes[0];
            if (progressBarEl && progressBarEl.instance) {
                this.progressBarInstance = progressBarEl.instance;
            }
        }
        
        // Инициализация
        this.state = {
            progress: 0
        };
        
        this.taskId = null;
        this.isConnectedToRoom = false;
        
        // Сохраняем экземпляр для доступа из других скриптов
        if (!document.app) {
            document.app = {};
        }
        document.app.highlightPageInstance = this;
        
        this.init();
    }
    
    /**
     * Инициализация элементов
     */
    init() {
        // Ждем загрузки DOM
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }
    
    /**
     * Настройка элементов страницы
     */
    setup() {
        // Если прогресс-бар еще не найден, пробуем найти снова
        if (!this.progressBarInstance) {
            const $progressBar = u('.js-progress-bar');
            if ($progressBar.length) {
                const progressBarEl = $progressBar.nodes[0];
                if (progressBarEl && progressBarEl.instance) {
                    this.progressBarInstance = progressBarEl.instance;
                }
            }
        }
        
        // Получаем task_id из URL параметров только если он еще не установлен
        if (!this.taskId) {
            const urlParams = new URLSearchParams(window.location.search);
            this.taskId = urlParams.get('task_id') || urlParams.get('check_task_id');
        }
        
        // Если есть task_id, подключаемся к Socket.IO комнате
        if (this.taskId) {
            this.connectToProgressRoom();
        }
        
        // Устанавливаем начальное значение
        this.updateView();
    }
    
    /**
     * Подключается к Socket.IO комнате прогресса задачи
     */
    async connectToProgressRoom() {
        if (!this.taskId) {
            return;
        }
        
        // Избегаем повторного подключения к той же комнате
        if (this.isConnectedToRoom) {
            return;
        }
        
        this.isConnectedToRoom = true;
        
        try {
            await socketIOService.joinTaskProgress(
                this.taskId,
                (data) => {
                    // Обновляем прогресс при получении события progress
                    console.log('Highlight: Progress event received:', data);
                    const progressValue = data.progress || 0;
                    console.log('Highlight: Setting progress to:', progressValue);
                    this.state.progress = progressValue;
                    this.updateView();
                },
                (data) => {
                    // Обработка события joined (опционально)
                    console.log('Highlight: Joined task progress room:', data);
                }
            );
            console.log('Highlight: Successfully joined task progress room for task:', this.taskId);
        } catch (error) {
            console.error('Highlight: Failed to join task progress room:', error);
            this.isConnectedToRoom = false;
        }
    }
    
    /**
     * Обновляет отображение прогресс-бара
     */
    updateView() {
        if (!this.progressBarInstance) {
            console.warn('Highlight: progressBarInstance not available');
            return;
        }
        
        // Устанавливаем значение в прогресс-бар из state
        // Прогресс приходит как процент (0-100), ProgressBar ожидает значение от 0 до max
        const progressValue = this.state.progress || 0;
        console.log('Highlight: Updating progress bar with value:', progressValue);
        this.progressBarInstance.setValue(progressValue);
    }
    
    /**
     * Устанавливает task_id и подключается к Socket.IO комнате прогресса
     * @param {string} taskId - ID задачи
     */
    async setTaskId(taskId) {
        if (!taskId) {
            return;
        }
        
        // Если task_id уже установлен и совпадает, не делаем ничего
        if (this.taskId === taskId && this.isConnectedToRoom) {
            return;
        }
        
        // Если был другой task_id, сбрасываем флаг подключения
        if (this.taskId !== taskId) {
            this.isConnectedToRoom = false;
        }
        
        this.taskId = taskId;
        
        // Убеждаемся, что прогресс-бар инициализирован
        if (!this.progressBarInstance) {
            this.setup();
        }
        
        // Подключаемся к комнате прогресса
        await this.connectToProgressRoom();
    }
}

// Создаем экземпляр при загрузке модуля
new Highlight();
