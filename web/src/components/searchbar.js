const d3 = Object.assign(
  {},
  require('d3-selection'),
);

export default class SearchBar {
  constructor(selectorId, argConfig) {
    this.selector = d3.select(selectorId);
    const config = argConfig || {};
    this.searchHandler = config.searchHandler;
    this._setupInputHandler();
  }

  onSearch(searchHandler) {
    this.searchHandler = searchHandler;
  }

  _setupInputHandler() {
    this.selector.on('keyup', (obj, i, nodes) => {
      const query = nodes[i].value.toLowerCase();
      this.searchHandler(query);
    });
  }

}
