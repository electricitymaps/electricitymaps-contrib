const d3 = Object.assign(
  {},
  require('d3-selection'),
);

const ENTER_KEY_CODE = 13;

export default class SearchBar {
  constructor(selectorId, argConfig) {
    this.selector = d3.select(selectorId);
    const config = argConfig || {};
    this.searchHandler = config.searchHandler;
    this.enterKeypressHandler = config.enterKeypressHandler;
    this._setupEventHandlers();
    this.inputNode = this.selector.node();
  }

  onSearch(searchHandler) {
    this.searchHandler = searchHandler;
  }

  onEnterKeypress(enterKeypressHandler) {
    this.enterKeypressHandler = enterKeypressHandler;
  }

  clearInputAndFocus() {
    this.inputNode.value = '';
    this.inputNode.focus();
  }

  focusWithInput(input) {
    if (!this.hasFocus()) {
      this.inputNode.value = this.inputNode.value + input;
      this.inputNode.focus();
    }
  }

  hasFocus() {
    return document.activeElement === this.inputNode;
  }

  _setupEventHandlers() {
    this.selector.on('keyup', (obj, i, nodes) => {
      if (this.searchHandler != null) {
        const query = nodes[i].value.toLowerCase();
        this.searchHandler(query);
      }
    });

    this.selector.node().addEventListener('keypress', (e) => {
      if (this.enterKeypressHandler != null && e.keyCode === ENTER_KEY_CODE) {
        this.enterKeypressHandler();
      }
    });
  }
}
