/**
 * Модуль для отображения ошибок в виде попапа
 */
const ErrorPopup = {
    // DOM-элементы
    popup: null,
    popupContent: null,
    errorDetails: null,
    closeButton: null,

    /**
     * Инициализация модуля
     */
    init: function() {
        // Создаем элементы попапа, если их ещё нет
        this.createPopupElements();
        
        // Устанавливаем обработчик для закрытия попапа
        this.closeButton.addEventListener('click', () => {
            this.hide();
        });
        
        // Закрытие по клику на заднем фоне
        this.popup.addEventListener('click', (e) => {
            if (e.target === this.popup) {
                this.hide();
            }
        });
        
        // Закрытие по клавише ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.popup.style.display === 'flex') {
                this.hide();
            }
        });
    },
    
    /**
     * Создает DOM-элементы попапа
     */
    createPopupElements: function() {
        if (document.getElementById('error-popup')) {
            // Элементы уже существуют, получаем их
            this.popup = document.getElementById('error-popup');
            this.popupContent = document.getElementById('error-message');
            this.errorDetails = document.getElementById('error-details');
            this.closeButton = document.getElementById('error-popup-close');
            return;
        }
        
        // Создаем попап
        this.popup = document.createElement('div');
        this.popup.id = 'error-popup';
        this.popup.className = 'popup-overlay';
        
        // Создаем контейнер для содержимого
        const popupContainer = document.createElement('div');
        popupContainer.className = 'popup-container';
        
        // Создаем заголовок
        const popupHeader = document.createElement('div');
        popupHeader.className = 'popup-header';
        
        const popupTitle = document.createElement('h3');
        popupTitle.textContent = 'Ошибка';
        
        this.closeButton = document.createElement('button');
        this.closeButton.id = 'error-popup-close';
        this.closeButton.className = 'popup-close';
        this.closeButton.innerHTML = '&times;';
        
        popupHeader.appendChild(popupTitle);
        popupHeader.appendChild(this.closeButton);
        
        // Создаем контент
        const popupContentContainer = document.createElement('div');
        popupContentContainer.className = 'popup-content';
        
        // Сообщение об ошибке
        this.popupContent = document.createElement('div');
        this.popupContent.id = 'error-message';
        this.popupContent.className = 'error-message';
        
        // Детали ошибки (техническая информация)
        this.errorDetails = document.createElement('div');
        this.errorDetails.id = 'error-details';
        this.errorDetails.className = 'error-details';
        this.errorDetails.style.display = 'none';
        
        // Собираем попап
        popupContentContainer.appendChild(this.popupContent);
        popupContentContainer.appendChild(this.errorDetails);
        
        popupContainer.appendChild(popupHeader);
        popupContainer.appendChild(popupContentContainer);
        this.popup.appendChild(popupContainer);
        
        // Добавляем в DOM
        document.body.appendChild(this.popup);
    },
    
    /**
     * Отображает попап с сообщением об ошибке
     * @param {string|object} error - Сообщение об ошибке или объект с ошибкой
     */
    show: function(error) {
        // Проверяем, что попап создан
        if (!this.popup) {
            this.init();
        }
        
        let userMessage = '';
        let technicalDetails = '';
        
        // Определяем тип ошибки и извлекаем нужную информацию
        if (typeof error === 'string') {
            userMessage = error;
            // Пробуем извлечь технические детали, если они есть в сообщении
            const errorParts = error.split('Ошибка: ');
            if (errorParts.length > 1) {
                userMessage = 'Произошла ошибка при обработке';
                technicalDetails = errorParts[1];
            }
        } else if (error instanceof Error) {
            userMessage = 'Произошла ошибка при обработке';
            technicalDetails = `${error.name}: ${error.message}\n${error.stack || ''}`;
        } else if (typeof error === 'object') {
            userMessage = error.message || 'Произошла ошибка при обработке';
            technicalDetails = error.error || error.details || JSON.stringify(error, null, 2);
        }
        
        // Устанавливаем сообщение
        this.popupContent.textContent = userMessage;
        
        // Отображаем технические детали, если они есть
        if (technicalDetails) {
            this.errorDetails.textContent = technicalDetails;
            this.errorDetails.style.display = 'block';
        } else {
            this.errorDetails.style.display = 'none';
        }
        
        // Показываем попап
        this.popup.style.display = 'flex';
        
        // Применяем анимацию
        setTimeout(() => {
            const container = this.popup.querySelector('.popup-container');
            container.classList.add('visible');
        }, 10);
    },
    
    /**
     * Скрывает попап
     */
    hide: function() {
        if (this.popup) {
            const container = this.popup.querySelector('.popup-container');
            container.classList.remove('visible');
            
            // Ждем окончания анимации перед скрытием
            setTimeout(() => {
                this.popup.style.display = 'none';
            }, 300);
        }
    }
};

// Инициализация модуля при загрузке документа
document.addEventListener('DOMContentLoaded', function() {
    ErrorPopup.init();
});