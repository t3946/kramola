/**
 * Базовый класс для всех компонентов
 * Предоставляет общую функциональность для работы с DOM и состоянием
 * Использует Umbrella.js для работы с DOM
 */
import u from 'umbrellajs';

class BaseComponent {
  constructor(el) {
    // Преобразуем элемент в Umbrella.js-объект
    if (typeof el === 'string') {
      this.$el = u(el);
    } else if (el && el.nodes) {
      // Это уже Umbrella.js объект
      this.$el = el;
    } else {
      this.$el = u(el);
    }
    
    if (!this.$el.length) throw new Error('Element not found');
    
    // Сохраняем нативный элемент для доступа к dataset и другим нативным свойствам
    this.el = this.$el.nodes[0];
    
    // Привязываем экземпляр к DOM-элементу
    this.el.instance = this;
    this._state = {};
  }

  state(newState) {
    // Обновление состояния
    if (newState) {
      this._state = { ...this._state, ...newState };
      this.updateView();
    }
    return this._state;
  }

  updateView() {
    // Перерисовка DOM на основе состояния
    // Переопределяется в дочерних классах
  }

  static register() {
    // Регистрация для автосканирования
    BaseComponent.components.push(this);
  }

  /**
   * Инициализирует все компоненты на странице
   * Сканирует страницу на компоненты и создает их экземпляры
   */
  static initComponents() {
    // Сканируем страницу на компоненты
    BaseComponent.components.forEach(ComponentClass => {
      const selector = `.${ComponentClass.commonClass}`;
      const $elements = u(selector);
      
      $elements.each((el) => {
        const $el = u(el);
        const nativeEl = $el.nodes[0];
        if (!nativeEl.instance) { // Избегаем повторной инициализации
          new ComponentClass($el);
        }
      });
    });
  }
}

// Глобальный реестр
BaseComponent.components = [];

export default BaseComponent;
