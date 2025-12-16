/**
 * Скрипт для страницы highlight
 * Управляет прогресс-баром на странице выделения слов
 */

import { Page } from './Page.js';
import socketIOService from '../services/SocketIOService.js';

class Highlight extends Page {
    constructor() {
        super();
        
        // Проверяем, что мы на нужной странице
        if (!this.isCurrentPage('/highlight', 'uploadForm', 'action', 'highlight')) {
            return;
        }
        
        // Инициализация
        this.state = {
            progress: 0
        };
        
        this.progressBarElement = null;
        this.progressBarInstance = null;
        this.taskId = null;
        
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
        // Находим progress bar элемент через DOM по классу
        const progressBarContainer = document.querySelector('.progressBarContainer');
        
        if (!progressBarContainer) {
            return;
        }

        // Находим сам прогресс-бар внутри контейнера
        this.progressBarElement = progressBarContainer.querySelector('.progress-bar-container');
        
        if (!this.progressBarElement || !this.progressBarElement.instance) {
            return;
        }

        // Получаем экземпляр
        this.progressBarInstance = this.progressBarElement.instance;
        
        // Получаем task_id из URL параметров
        const urlParams = new URLSearchParams(window.location.search);
        this.taskId = urlParams.get('task_id') || urlParams.get('check_task_id');
        
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
    connectToProgressRoom() {
        if (!this.taskId) {
            return;
        }
        
        socketIOService.joinTaskProgress(
            this.taskId,
            (data) => {
                // Обновляем прогресс при получении события progress
                this.state.progress = data.progress || 0;
                this.updateView();
            },
            (data) => {
                // Обработка события joined (опционально)
            }
        );
    }
    
    /**
     * Обновляет отображение прогресс-бара
     */
    updateView() {
        if (!this.progressBarInstance) {
            return;
        }
        
        // Устанавливаем значение в прогресс-бар из state
        this.progressBarInstance.setValue(this.state.progress);
    }
}

// Создаем экземпляр при загрузке модуля
new Highlight();
