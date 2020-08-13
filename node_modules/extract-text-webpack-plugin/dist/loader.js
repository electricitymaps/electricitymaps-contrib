'use strict';

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.pitch = pitch;

var _fs = require('fs');

var _fs2 = _interopRequireDefault(_fs);

var _path = require('path');

var _path2 = _interopRequireDefault(_path);

var _loaderUtils = require('loader-utils');

var _loaderUtils2 = _interopRequireDefault(_loaderUtils);

var _NodeTemplatePlugin = require('webpack/lib/node/NodeTemplatePlugin');

var _NodeTemplatePlugin2 = _interopRequireDefault(_NodeTemplatePlugin);

var _NodeTargetPlugin = require('webpack/lib/node/NodeTargetPlugin');

var _NodeTargetPlugin2 = _interopRequireDefault(_NodeTargetPlugin);

var _LibraryTemplatePlugin = require('webpack/lib/LibraryTemplatePlugin');

var _LibraryTemplatePlugin2 = _interopRequireDefault(_LibraryTemplatePlugin);

var _SingleEntryPlugin = require('webpack/lib/SingleEntryPlugin');

var _SingleEntryPlugin2 = _interopRequireDefault(_SingleEntryPlugin);

var _LimitChunkCountPlugin = require('webpack/lib/optimize/LimitChunkCountPlugin');

var _LimitChunkCountPlugin2 = _interopRequireDefault(_LimitChunkCountPlugin);

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

/* eslint-disable
  consistent-return,
  no-param-reassign
*/
const NS = _path2.default.dirname(_fs2.default.realpathSync(__filename));
const plugin = { name: 'ExtractTextPlugin' };

exports.default = source => source;

function pitch(request) {
  const query = _loaderUtils2.default.getOptions(this) || {};
  let loaders = this.loaders.slice(this.loaderIndex + 1);
  this.addDependency(this.resourcePath);

  // We already in child compiler, return empty bundle
  // eslint-disable-next-line no-undefined
  if (this[NS] === undefined) {
    throw new Error('"extract-text-webpack-plugin" loader is used without the corresponding plugin, ' + 'refer to https://github.com/webpack/extract-text-webpack-plugin for the usage example');
  } else if (this[NS] === false) {
    return '';
  } else if (this[NS](null, query)) {
    if (query.omit) {
      this.loaderIndex += +query.omit + 1;
      request = request.split('!').slice(+query.omit).join('!');
      loaders = loaders.slice(+query.omit);
    }

    let resultSource;
    if (query.remove) {
      resultSource = '// removed by extract-text-webpack-plugin';
    } else {
      resultSource = undefined; // eslint-disable-line no-undefined
    }

    const childFilename = 'extract-text-webpack-plugin-output-filename'; // eslint-disable-line no-path-concat
    const publicPath = typeof query.publicPath === 'string' ? query.publicPath : this._compilation.outputOptions.publicPath;
    const outputOptions = {
      filename: childFilename,
      publicPath
    };

    const childCompiler = this._compilation.createChildCompiler(`extract-text-webpack-plugin ${NS} ${request}`, outputOptions);

    new _NodeTemplatePlugin2.default(outputOptions).apply(childCompiler);
    new _LibraryTemplatePlugin2.default(null, 'commonjs2').apply(childCompiler);
    new _NodeTargetPlugin2.default().apply(childCompiler);
    new _SingleEntryPlugin2.default(this.context, `!!${request}`).apply(childCompiler);
    new _LimitChunkCountPlugin2.default({ maxChunks: 1 }).apply(childCompiler);

    // We set loaderContext[NS] = false to indicate we already in
    // a child compiler so we don't spawn other child compilers from there.
    childCompiler.hooks.thisCompilation.tap(plugin, compilation => {
      compilation.hooks.normalModuleLoader.tap(plugin, (loaderContext, module) => {
        loaderContext[NS] = false;
        if (module.request === request) {
          module.loaders = loaders.map(loader => {
            return {
              loader: loader.path,
              options: loader.options
            };
          });
        }
      });
    });

    let source;
    childCompiler.hooks.afterCompile.tap(plugin, compilation => {
      source = compilation.assets[childFilename] && compilation.assets[childFilename].source();

      // Remove all chunk assets
      compilation.chunks.forEach(chunk => {
        chunk.files.forEach(file => {
          delete compilation.assets[file];
        });
      });
    });

    const callback = this.async();
    childCompiler.runAsChild((err, entries, compilation) => {
      if (err) return callback(err);

      if (compilation.errors.length > 0) {
        return callback(compilation.errors[0]);
      }

      compilation.fileDependencies.forEach(dep => {
        this.addDependency(dep);
      }, this);

      compilation.contextDependencies.forEach(dep => {
        this.addContextDependency(dep);
      }, this);

      if (!source) {
        return callback(new Error("Didn't get a result from child compiler"));
      }

      try {
        let text = this.exec(source, request);

        if (typeof text === 'string') {
          text = [[compilation.entries[0].identifier(), text]];
        } else {
          text.forEach(item => {
            const [id] = item;

            compilation.modules.forEach(module => {
              if (module.id === id) {
                item[0] = module.identifier();
              }
            });
          });
        }

        this[NS](text, query);

        // NOTE: converting this to ESM will require changes to renderExtractedChunk
        if (text.locals && typeof resultSource !== 'undefined') {
          resultSource += `\nmodule.exports = ${JSON.stringify(text.locals)};`;
        }
      } catch (e) {
        return callback(e);
      }

      if (resultSource) {
        callback(null, resultSource);
      } else {
        callback();
      }
    });
  }
}