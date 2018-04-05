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
    this._setupInputHandler();
  }

  onSearch(searchHandler) {
    this.searchHandler = searchHandler;
  }

  onEnterKeypress(enterKeypressHandler) {
    this.enterKeypressHandler = enterKeypressHandler;
  }

  _setupInputHandler() {
    this.selector.on('keyup', (obj, i, nodes) => {
      const query = nodes[i].value.toLowerCase();
      this.searchHandler(query);
    });
    this.selector.node().addEventListener('keypress', (e) => {
      if (e.keyCode === ENTER_KEY_CODE) {
        this.enterKeypressHandler();
      }
    });
  }
}
