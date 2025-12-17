/**
 * ProgressBar component
 * Displays progress bar with configurable value, color and label
 */
import BaseComponent from './BaseComponent.js';
import u from 'umbrellajs';

class ProgressBar extends BaseComponent {
  /**
   * @param {HTMLElement|string} el
   */
  constructor(el) {
    super(el);
    
    const valueAttr = this.$el.attr('data-value');
    const maxAttr = this.$el.attr('data-max');
    const colorAttr = this.$el.attr('data-color');
    const labelAttr = this.$el.attr('data-label');
    const showPercentageAttr = this.$el.attr('data-show-percentage');
    
    const initialValue = valueAttr !== undefined ? parseFloat(valueAttr) : 0;
    const initialMax = maxAttr !== undefined ? parseFloat(maxAttr) : 100;
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
    const percentage = (value / max) * 100;
    
    this.el.style.setProperty('--progress-value', value);
    this.el.style.setProperty('--progress-max', max);
    this.el.style.setProperty('--progress-percentage', `${percentage}%`);
    this.el.style.setProperty('--progress-color', color);
    
    this.$el.attr({
      'role': 'progressbar',
      'aria-valuenow': value,
      'aria-valuemin': 0,
      'aria-valuemax': max
    });
    
    const $fillEl = this.$el.find('.progress-bar-fill');
    if ($fillEl.length) {
      $fillEl.nodes[0].style.width = `${percentage}%`;
      
      const $wrapper = this.$el.find('.progress-bar-wrapper');
      const textEl = $wrapper.nodes[0]?.querySelector('.progress-bar-text');
      if (showPercentage && textEl) {
        textEl.textContent = `${Math.round(percentage)}%`;
      }
    }
    
    const $labelEl = this.$el.find('.progress-bar-label');
    if (label) {
      if (!$labelEl.length) {
        const $newLabel = u('<div>').addClass('progress-bar-label');
        this.$el.prepend($newLabel);
        $newLabel.text(label);
      } else {
        $labelEl.text(label);
      }
    } else {
      $labelEl.remove();
    }
  }

  /**
   * @param {Object} newState
   * @returns {Object}
   */
  state(newState) {
    return super.state(newState);
  }

  /**
   * @param {number} value
   */
  setValue(value) {
    const { max } = this.state();
    const clampedValue = Math.max(0, Math.min(max, value));
    this.state({ value: clampedValue });
  }

  /**
   * @returns {number}
   */
  getValue() {
    return this.state().value;
  }

  /**
   * @param {number} max
   */
  setMax(max) {
    this.state({ max: Math.max(1, max) });
  }

  /**
   * @returns {number}
   */
  getMax() {
    return this.state().max;
  }

  /**
   * @param {string} color
   */
  setColor(color) {
    this.state({ color });
  }

  /**
   * @returns {string}
   */
  getColor() {
    return this.state().color;
  }

  /**
   * @param {string} label
   */
  setLabel(label) {
    this.state({ label });
  }

  /**
   * @returns {string}
   */
  getLabel() {
    return this.state().label;
  }

  /**
   * @param {boolean} show
   */
  showPercentage(show) {
    this.state({ showPercentage: show });
  }

  static commonClass = 'js-progress-bar';
}

ProgressBar.register();

export default ProgressBar;
