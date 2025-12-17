/**
 * Базовый класс для страниц
 * Предоставляет общую функциональность проверки страницы
 * Использует Umbrella.js для работы с DOM
 */
import u from 'umbrellajs';

export class Page {
    /**
     * Проверяет, является ли текущая страница нужной страницей
     * @param {string} pathPattern - Паттерн пути для проверки
     * @param {string} elementId - ID элемента для проверки
     * @param {string} elementAttribute - Атрибут элемента для проверки
     * @param {string} attributePattern - Паттерн атрибута
     * @returns {boolean}
     */
    isCurrentPage(pathPattern, elementId, elementAttribute, attributePattern) {
        // Проверяем URL
        const path = window.location.pathname;
        if (pathPattern && path.includes(pathPattern)) {
            return true;
        }
        
        // Проверяем наличие специфичных элементов страницы
        if (elementId && elementAttribute && attributePattern) {
            const $element = u(`#${elementId}`);
            if ($element.length) {
                const attributeValue = $element.attr(elementAttribute) || '';
                if (attributeValue.includes(attributePattern)) {
                    return true;
                }
            }
        }
        
        return false;
    }
}
