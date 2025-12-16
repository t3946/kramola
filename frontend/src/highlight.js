/**
 * Скрипт для страницы highlight
 * Управляет прогресс-баром на странице выделения слов
 */

import ProgressBar from './components/progress-bar.js';

(function() {
    'use strict';

    /**
     * Проверяет, является ли текущая страница страницей highlight
     * @returns {boolean}
     */
    function isHighlightPage() {
        // Проверяем URL
        const path = window.location.pathname;

        if (path.includes('/highlight')) {
            return true;
        }
        
        // Проверяем наличие специфичных элементов страницы highlight
        const uploadForm = document.getElementById('uploadForm');

        if (uploadForm) {
            const formAction = uploadForm.getAttribute('action') || '';
            if (formAction.includes('highlight')) {
                return true;
            }
        }
        
        return false;
    }

    /**
     * Инициализация скрипта для страницы highlight
     */
    function init() {
        // Проверяем, что мы на нужной странице
        if (!isHighlightPage()) {
            return;
        }

        // Ждем загрузки DOM
        function setup() {
            // Находим progress bar элемент через DOM по классу
            const progressBarContainer = document.querySelector('.progressBarContainer');
            
            if (!progressBarContainer) {
                console.warn('Highlight: progress bar container не найден');
                return;
            }

            // Находим сам прогресс-бар внутри контейнера
            const progressBarElement = progressBarContainer.querySelector('.progress-bar-container');
            
            if (!progressBarElement) {
                console.warn('Highlight: progress bar элемент не найден');
                return;
            }

            // Получаем ссылку на объект конструктора из progress-bar.js
            // Ссылка сохраняется в DOM элементе через element.instance
            let progressBarInstance = progressBarElement.instance;
            
            // Если экземпляр еще не создан, инициализируем его через ProgressBar.initFromElement
            if (!progressBarInstance) {
                progressBarInstance = ProgressBar.initFromElement(progressBarElement, {
                    label: 'Прогресс обработки',
                    color: 'primary',
                    showPercentage: true,
                    animated: true
                });

                if (!progressBarInstance) {
                    console.warn('Highlight: не удалось инициализировать progress bar');
                    return;
                }
            }

            // Выполняем простое действие - устанавливаем прогресс 50%
            if (progressBarInstance) {
                progressBarInstance.setValue(50);
                console.log('Highlight: прогресс установлен на 50%');
            }
        }

        // Запускаем настройку после загрузки DOM
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', setup);
        } else {
            setup();
        }
    }

    // Запускаем инициализацию
    init();
})();
