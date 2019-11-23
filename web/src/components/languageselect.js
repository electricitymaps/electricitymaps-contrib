const d3 = Object.assign(
  {},
  require('d3-array'),
  require('d3-collection'),
  require('d3-selection'),
);

const { languageNames } = require('../../locales-config.json');

export default class LanguageSelect {
  constructor(selectorId) {
    this.selectorId = selectorId;
    this.visibleListItems = [];
  }


  render() {
    this._createListItems();
    this._setItemNames();
    this._setItemClickHandlers();
  }

  _createListItems() {
    this.selector = d3.select(this.selectorId)
      .selectAll('li')
      .data(Object.entries(languageNames));

    const itemLinks = this.selector.enter().append('li');

    this.visibleListItems = itemLinks.nodes();
    this.selector = itemLinks.merge(this.selector);
  }

  _setItemNames() {
    this.selector.text(([key, language]) => language);
  }

  _setItemClickHandlers() {
    if (window.isCordova) {
      this.selector.on('click', ([key, language]) => { window.location.href = `index_${key}.html`; });
    } else {
      this.selector.on('click', ([key, language]) => { window.location.href = `${window.location.href}&lang=${key}`; });
    }
  }
}
