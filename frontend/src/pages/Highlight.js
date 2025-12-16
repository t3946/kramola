/**
 * Скрипт для страницы highlight
 * Управляет прогресс-баром на странице выделения слов
 */

import { Page } from './Page.js';

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
        
        // Устанавливаем начальное значение
        this.updateView();
    }
    
    /**
     * Обновляет отображение прогресс-бара
     */
    updateView() {
        if (!this.progressBarInstance) {
            return;
        }
        
        // Обновляем состояние
        this.state.progress = 50;
        
        // Устанавливаем значение в прогресс-бар
        this.progressBarInstance.setValue(this.state.progress);
    }
}

// Создаем экземпляр при загрузке модуля
new Highlight();
