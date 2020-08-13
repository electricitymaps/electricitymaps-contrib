'use strict';

Object.defineProperty(exports, "__esModule", {
  value: true
});

var _webpackSources = require('webpack-sources');

class ExtractedModule {
  constructor(identifier, originalModule, source, sourceMap, additionalInformation, prevModules) {
    this._identifier = identifier;
    this._originalModule = originalModule;
    this._source = source;
    this._sourceMap = sourceMap;
    this._prevModules = prevModules;
    this.additionalInformation = additionalInformation;
    this.chunks = [];
  }

  getOrder() {
    // http://stackoverflow.com/a/14676665/1458162
    return (/^@import url/.test(this._source) ? 0 : 1
    );
  }

  addChunk(chunk) {
    const idx = this.chunks.indexOf(chunk);
    if (idx < 0) {
      this.chunks.push(chunk);
    }
  }

  removeChunk(chunk) {
    const idx = this.chunks.indexOf(chunk);
    if (idx >= 0) {
      this.chunks.splice(idx, 1);
      chunk.removeModule(this);
      return true;
    }
    return false;
  }

  rewriteChunkInReasons(oldChunk, newChunks) {} // eslint-disable-line

  identifier() {
    return this._identifier;
  }

  source() {
    if (this._sourceMap) {
      return new _webpackSources.SourceMapSource(this._source, null, this._sourceMap);
    }
    return new _webpackSources.RawSource(this._source);
  }

  getOriginalModule() {
    return this._originalModule;
  }

  getPrevModules() {
    return this._prevModules;
  }

  addPrevModules(prevModules) {
    prevModules.forEach(m => {
      if (this._prevModules.indexOf(m) < 0) {
        this._prevModules.push(m);
      }
    }, this);
  }

  setOriginalModule(originalModule) {
    this._originalModule = originalModule;
  }
}

exports.default = ExtractedModule;