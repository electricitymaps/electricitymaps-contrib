const translation = require('../helpers/translation');

const d3 = Object.assign(
  {},
  require('d3-array'),
  require('d3-collection'),
  require('d3-selection'),
);

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
      .data(translation.languageNames);

    const itemLinks = this.selector.enter().append('li');

    this.visibleListItems = itemLinks.nodes();
    this.selector = itemLinks.merge(this.selector);
  }

  _setItemNames() {
    this.selector.text(language => language.name);
  }

  _setItemClickHandlers() {
    if(window.isCordova){
      this.selector.on('click', language => window.location.href = `index_${language.shortName}.html`);
    }else{
      this.selector.on('click', language => window.location.href = `${window.location.href}&lang=${language.shortName}`);
    }
  }
}
