/**
 * Модуль компонента ProgressBar
 * Предоставляет функциональность для отображения прогресс-бара
 */
const ProgressBar = {
    /**
     * Создает новый экземпляр прогресс-бара
     * @param {string|HTMLElement} container - Селектор или DOM-элемент контейнера
     * @param {object} options - Опции для прогресс-бара
     * @param {string} options.label - Текст метки (по умолчанию: '')
     * @param {number} options.value - Начальное значение (0-100, по умолчанию: 0)
     * @param {string} options.color - Цвет прогресс-бара ('primary', 'success', 'warning', 'danger', по умолчанию: 'primary')
     * @param {boolean} options.showPercentage - Показывать ли процент (по умолчанию: true)
     * @param {boolean} options.animated - Использовать ли анимацию (по умолчанию: true)
     * @returns {object} Объект с методами управления прогресс-баром
     */
    create: function(container, options = {}) {
        const config = {
            label: options.label || '',
            value: Math.max(0, Math.min(100, options.value || 0)),
            color: options.color || 'primary',
            showPercentage: options.showPercentage !== false,
            animated: options.animated !== false
        };

        // Получаем контейнер
        const containerEl = typeof container === 'string' 
            ? document.querySelector(container) 
            : container;

        if (!containerEl) {
            console.error('ProgressBar: контейнер не найден');
            return null;
        }

        // Создаем структуру DOM
        const progressBarHTML = `
            <div class="progress-bar-container">
                ${config.label ? `<div class="progress-bar-label">${config.label}</div>` : ''}
                <div class="progress-bar-wrapper">
                    <div class="progress-bar-fill ${config.animated ? 'animated' : ''} progress-bar-${config.color}" 
                         style="width: ${config.value}%">
                        ${config.showPercentage ? `<span class="progress-bar-text">${Math.round(config.value)}%</span>` : ''}
                    </div>
                </div>
            </div>
        `;

        containerEl.innerHTML = progressBarHTML;
        const progressBarEl = containerEl.querySelector('.progress-bar-container');
        const fillEl = progressBarEl.querySelector('.progress-bar-fill');

        // Создаем объект с методами управления
        const progressBarInstance = {
            /**
             * Устанавливает значение прогресса
             * @param {number} value - Значение от 0 до 100
             * @param {number} duration - Длительность анимации в мс (по умолчанию: 300)
             */
            setValue: function(value) {
                const newValue = Math.max(0, Math.min(100, value));
                fillEl.style.width = `${newValue}%`;
                
                if (config.showPercentage) {
                    const textEl = fillEl.querySelector('.progress-bar-text');
                    if (textEl) {
                        textEl.textContent = `${Math.round(newValue)}%`;
                    }
                }
            },

            /**
             * Получает текущее значение прогресса
             * @returns {number} Текущее значение (0-100)
             */
            getValue: function() {
                const width = parseFloat(fillEl.style.width) || 0;
                return width;
            },

            /**
             * Устанавливает текст метки
             * @param {string} label - Текст метки
             */
            setLabel: function(label) {
                let labelEl = progressBarEl.querySelector('.progress-bar-label');
                if (label) {
                    if (!labelEl) {
                        labelEl = document.createElement('div');
                        labelEl.className = 'progress-bar-label';
                        progressBarEl.insertBefore(labelEl, progressBarEl.firstChild);
                    }
                    labelEl.textContent = label;
                } else if (labelEl) {
                    labelEl.remove();
                }
                config.label = label;
            },

            /**
             * Устанавливает цвет прогресс-бара
             * @param {string} color - Цвет ('primary', 'success', 'warning', 'danger')
             */
            setColor: function(color) {
                fillEl.classList.remove('progress-bar-primary', 'progress-bar-success', 'progress-bar-warning', 'progress-bar-danger');
                fillEl.classList.add(`progress-bar-${color}`);
                config.color = color;
            },

            /**
             * Показывает/скрывает процент
             * @param {boolean} show - Показывать ли процент
             */
            showPercentage: function(show) {
                config.showPercentage = show;
                const textEl = fillEl.querySelector('.progress-bar-text');
                if (show) {
                    if (!textEl) {
                        const span = document.createElement('span');
                        span.className = 'progress-bar-text';
                        span.textContent = `${Math.round(this.getValue())}%`;
                        fillEl.appendChild(span);
                    }
                } else if (textEl) {
                    textEl.remove();
                }
            },

            /**
             * Удаляет прогресс-бар из DOM
             */
            destroy: function() {
                progressBarEl.remove();
            },

            /**
             * Получает DOM-элемент прогресс-бара
             * @returns {HTMLElement} DOM-элемент
             */
            getElement: function() {
                return progressBarEl;
            }
        };

        // Сохраняем ссылку на экземпляр в DOM элементе для доступа из других скриптов
        progressBarEl.instance = progressBarInstance;
        // Также сохраняем в контейнере, если он не является самим progressBarEl
        if (containerEl !== progressBarEl) {
            containerEl.instance = progressBarInstance;
        }

        return progressBarInstance;
    },

    /**
     * Инициализирует экземпляр прогресс-бара на существующем DOM элементе
     * @param {string|HTMLElement} element - Селектор или DOM-элемент прогресс-бара
     * @param {object} options - Опции для прогресс-бара
     * @returns {object} Объект с методами управления прогресс-баром
     */
    initFromElement: function(element, options = {}) {
        const elementEl = typeof element === 'string' 
            ? document.querySelector(element) 
            : element;

        if (!elementEl) {
            console.error('ProgressBar: элемент не найден');
            return null;
        }

        // Если экземпляр уже существует, возвращаем его
        if (elementEl.instance) {
            return elementEl.instance;
        }

        // Находим элементы структуры
        const fillEl = elementEl.querySelector('.progress-bar-fill');
        if (!fillEl) {
            console.error('ProgressBar: структура прогресс-бара не найдена в элементе');
            return null;
        }

        const config = {
            label: options.label || '',
            value: options.value !== undefined ? Math.max(0, Math.min(100, options.value)) : parseFloat(fillEl.style.width) || 0,
            color: options.color || 'primary',
            showPercentage: options.showPercentage !== false,
            animated: options.animated !== false
        };

        // Создаем объект с методами управления
        const progressBarInstance = {
            setValue: function(value) {
                const newValue = Math.max(0, Math.min(100, value));
                fillEl.style.width = `${newValue}%`;
                
                if (config.showPercentage) {
                    const textEl = fillEl.querySelector('.progress-bar-text');
                    if (textEl) {
                        textEl.textContent = `${Math.round(newValue)}%`;
                    }
                }
            },

            getValue: function() {
                return parseFloat(fillEl.style.width) || 0;
            },

            setLabel: function(label) {
                let labelEl = elementEl.querySelector('.progress-bar-label');
                if (label) {
                    if (!labelEl) {
                        labelEl = document.createElement('div');
                        labelEl.className = 'progress-bar-label';
                        elementEl.insertBefore(labelEl, elementEl.firstChild);
                    }
                    labelEl.textContent = label;
                } else if (labelEl) {
                    labelEl.remove();
                }
                config.label = label;
            },

            setColor: function(color) {
                fillEl.classList.remove('progress-bar-primary', 'progress-bar-success', 'progress-bar-warning', 'progress-bar-danger');
                fillEl.classList.add(`progress-bar-${color}`);
                config.color = color;
            },

            showPercentage: function(show) {
                config.showPercentage = show;
                const textEl = fillEl.querySelector('.progress-bar-text');
                if (show) {
                    if (!textEl) {
                        const span = document.createElement('span');
                        span.className = 'progress-bar-text';
                        span.textContent = `${Math.round(this.getValue())}%`;
                        fillEl.appendChild(span);
                    }
                } else if (textEl) {
                    textEl.remove();
                }
            },

            destroy: function() {
                elementEl.remove();
            },

            getElement: function() {
                return elementEl;
            }
        };

        // Сохраняем ссылку на экземпляр в DOM элементе
        elementEl.instance = progressBarInstance;

        return progressBarInstance;
    },

    /**
     * Автоматически инициализирует все прогресс-бары на странице
     */
    initAuto: function() {
        // Находим все элементы с классом progress-bar-container
        const progressBars = document.querySelectorAll('.progress-bar-container');
        
        progressBars.forEach((barElement) => {
            // Если экземпляр уже существует, пропускаем
            if (barElement.instance) {
                return;
            }
            
            // Инициализируем экземпляр на существующем элементе
            // Получаем параметры из data-атрибутов или используем значения по умолчанию
            const options = {
                label: barElement.dataset.label || '',
                value: barElement.dataset.value !== undefined ? parseFloat(barElement.dataset.value) : undefined,
                color: barElement.dataset.color || 'primary',
                showPercentage: barElement.dataset.showPercentage !== 'false',
                animated: barElement.dataset.animated !== 'false'
            };
            
            this.initFromElement(barElement, options);
        });
    }
};

// Экспортируем для использования в других модулях
export default ProgressBar;

// Автоматическая инициализация при загрузке документа
document.addEventListener('DOMContentLoaded', function() {
    ProgressBar.initAuto();
});
