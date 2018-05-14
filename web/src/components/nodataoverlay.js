const translation = require('../helpers/translation');

const d3 = Object.assign(
  {},
  require('d3-selection'),
);

export default class NoDataOverlay {
  constructor(selectorId, argConfig) {
    this.selectorId = selectorId;
    this._setup();
  }

  _setup() {
    this.rootContainer = d3.select(this.selectorId).append('div').attr('class', 'no-data-overlay');
    this.overlayBackground = this.rootContainer.append('div').attr('class', 'overlay no-data-overlay-background');
    this.overlayTextBox = this.rootContainer.append('div').attr('class', 'no-data-overlay-message');
  }

  text(text) {
    this.overlayTextBox.text(text);
  }

  showIfElseHide(condition) {
    this.rootContainer.classed('visible', condition);
  }

}
