'use strict';

Object.defineProperty(exports, "__esModule", {
  value: true
});

var _ExtractedModule = require('./ExtractedModule');

var _ExtractedModule2 = _interopRequireDefault(_ExtractedModule);

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

class ExtractTextPluginCompilation {
  constructor() {
    this.modulesByIdentifier = {};
  }

  addModule(identifier, originalModule, source, additionalInformation, sourceMap, prevModules) {
    let m;

    if (!this.modulesByIdentifier[identifier]) {
      m = this.modulesByIdentifier[identifier] = new _ExtractedModule2.default(identifier, originalModule, source, sourceMap, additionalInformation, prevModules);
    } else {
      m = this.modulesByIdentifier[identifier];
      m.addPrevModules(prevModules);

      if (originalModule.index2 < m.getOriginalModule().index2) {
        m.setOriginalModule(originalModule);
      }
    }

    return m;
  }

  addResultToChunk(identifier, result, originalModule, extractedChunk) {
    if (!Array.isArray(result)) {
      result = [[identifier, result]];
    }

    const counterMap = {};
    const prevModules = [];

    result.forEach(item => {
      const c = counterMap[item[0]];
      const module = this.addModule.call(this, item[0] + (c || ''), originalModule, item[1], item[2], item[3], prevModules.slice());

      extractedChunk.addModule(module);
      // extractedChunk.removeModule(originalModule);
      module.addChunk(extractedChunk);
      counterMap[item[0]] = (c || 0) + 1;
      prevModules.push(module);
    }, this);
  }
} /* eslint-disable
    no-multi-assign,
    no-param-reassign
  */
exports.default = ExtractTextPluginCompilation;