/**
 * Компонент ProgressBar
 * Отображает прогресс-бар с возможностью настройки значения, цвета и метки
 * Использует Umbrella.js для работы с DOM
 */
import BaseComponent from './BaseComponent.js';
import u from 'umbrellajs';

class ProgressBar extends BaseComponent {
  constructor(el) {
    super(el);
    
    // Инициализируем состояние из data-атрибутов или значений по умолчанию
    // Используем attr() для более надежной работы с data-атрибутами
    const valueAttr = this.$el.attr('data-value');
    const maxAttr = this.$el.attr('data-max');
    const colorAttr = this.$el.attr('data-color');
    const labelAttr = this.$el.attr('data-label');
    const showPercentageAttr = this.$el.attr('data-show-percentage');
    
    const initialValue = valueAttr !== undefined 
      ? parseFloat(valueAttr) 
      : 0;
    const initialMax = maxAttr !== undefined 
      ? parseFloat(maxAttr) 
      : 100;
    const initialColor = colorAttr || '#4CAF50';
    const initialLabel = labelAttr || '';
    
    this.state({
      value: Math.max(0, Math.min(initialMax, initialValue)),
      max: initialMax,
      color: initialColor,
      label: initialLabel,
      showPercentage: showPercentageAttr !== 'false'
    });
    
    this.init();
  }

  init() {
    // Создаем структуру DOM, если её еще нет
    if (!this.$el.find('.progress-bar-wrapper').length) {
      this.createDOMStructure();
    }
    this.updateView();
  }

  createDOMStructure() {
    const { label } = this.state();
    
    const $wrapper = u('<div>').addClass('progress-bar-wrapper');
    const $fill = u('<div>').addClass('progress-bar-fill');
    
    $wrapper.append($fill);
    
    if (label) {
      const $label = u('<div>')
        .addClass('progress-bar-label')
        .text(label);
      this.$el.prepend($label);
    }
    
    this.$el.append($wrapper);
  }

  updateView() {
    const { value, max, color, label, showPercentage } = this.state();
    
    // Обновляем CSS переменные
    const percentage = (value / max) * 100;
    this.$el.css({
      '--progress-value': value,
      '--progress-max': max,
      '--progress-percentage': `${percentage}%`,
      '--progress-color': color
    });
    
    // Обновляем aria-атрибуты для доступности
    this.$el.attr({
      'role': 'progressbar',
      'aria-valuenow': value,
      'aria-valuemin': 0,
      'aria-valuemax': max
    });
    
    // Обновляем визуальное отображение
    const $fillEl = this.$el.find('.progress-bar-fill');
    if ($fillEl.length) {
      $fillEl.css({
        'width': `${percentage}%`,
        'background-color': color
      });
      
      // Обновляем текст процента
      let $textEl = $fillEl.find('.progress-bar-text');
      if (showPercentage) {
        if (!$textEl.length) {
          $textEl = u('<span>').addClass('progress-bar-text');
          $fillEl.append($textEl);
        }
        $textEl.text(`${Math.round(percentage)}%`);
      } else {
        $textEl.remove();
      }
    }
    
    // Обновляем метку
    let $labelEl = this.$el.find('.progress-bar-label');
    if (label) {
      if (!$labelEl.length) {
        $labelEl = u('<div>').addClass('progress-bar-label');
        this.$el.prepend($labelEl);
      }
      $labelEl.text(label);
    } else {
      $labelEl.remove();
    }
  }

  state(newState) {
    return super.state(newState);
  }

  // Публичные методы для удобства использования
  setValue(value) {
    const { max } = this.state();
    this.state({ value: Math.max(0, Math.min(max, value)) });
  }

  getValue() {
    return this.state().value;
  }

  setMax(max) {
    this.state({ max: Math.max(1, max) });
  }

  getMax() {
    return this.state().max;
  }

  setColor(color) {
    this.state({ color });
  }

  getColor() {
    return this.state().color;
  }

  setLabel(label) {
    this.state({ label });
  }

  getLabel() {
    return this.state().label;
  }

  showPercentage(show) {
    this.state({ showPercentage: show });
  }

  static commonClass = 'js-progress-bar';
}

// Обязательная регистрация
ProgressBar.register();

export default ProgressBar;
