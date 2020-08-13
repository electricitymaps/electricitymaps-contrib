'use strict';

Object.defineProperty(exports, "__esModule", {
  value: true
});

var _fs = require('fs');

var _fs2 = _interopRequireDefault(_fs);

var _path = require('path');

var _path2 = _interopRequireDefault(_path);

var _Chunk = require('webpack/lib/Chunk');

var _Chunk2 = _interopRequireDefault(_Chunk);

var _webpackSources = require('webpack-sources');

var _async = require('async');

var _async2 = _interopRequireDefault(_async);

var _loaderUtils = require('loader-utils');

var _loaderUtils2 = _interopRequireDefault(_loaderUtils);

var _schemaUtils = require('schema-utils');

var _schemaUtils2 = _interopRequireDefault(_schemaUtils);

var _ExtractTextPluginCompilation = require('./lib/ExtractTextPluginCompilation');

var _ExtractTextPluginCompilation2 = _interopRequireDefault(_ExtractTextPluginCompilation);

var _OrderUndefinedError = require('./lib/OrderUndefinedError');

var _OrderUndefinedError2 = _interopRequireDefault(_OrderUndefinedError);

var _helpers = require('./lib/helpers');

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

/* eslint-disable
  consistent-return,
  no-param-reassign,
  prefer-rest-params
*/
const NS = _path2.default.dirname(_fs2.default.realpathSync(__filename));
const plugin = { name: 'ExtractTextPlugin' };

let nextId = 0;

class ExtractTextPlugin {
  constructor(options) {
    if ((0, _helpers.isString)(options)) {
      options = { filename: options };
    } else {
      (0, _schemaUtils2.default)(_path2.default.resolve(__dirname, './plugin.json'), options, 'Extract Text Plugin');
    }
    this.filename = options.filename;
    this.id = options.id != null ? options.id : nextId += 1;
    this.options = {};
    (0, _helpers.mergeOptions)(this.options, options);
    delete this.options.filename;
    delete this.options.id;
  }

  static loader(options) {
    return { loader: require.resolve('./loader'), options };
  }

  static applyAdditionalInformation(source, info) {
    if (info) {
      return new _webpackSources.ConcatSource(`@media ${info[0]} {`, source, '}');
    }

    return source;
  }

  loader(options) {
    return ExtractTextPlugin.loader((0, _helpers.mergeOptions)({ id: this.id }, options));
  }

  mergeNonInitialChunks(chunk, intoChunk, checkedChunks) {
    if (!intoChunk) {
      const newCheckedChunks = [];

      for (const asyncChunk of chunk.getAllAsyncChunks()) {
        if (!asyncChunk.isOnlyInitial()) {
          this.mergeNonInitialChunks(asyncChunk, chunk, newCheckedChunks);
        }
      }
    } else if (!checkedChunks.includes(chunk)) {
      const newCheckedChunks = checkedChunks.concat(chunk);

      for (const chunkModule of chunk.modulesIterable) {
        intoChunk.addModule(chunkModule);
        chunkModule.addChunk(intoChunk);
      }

      for (const asyncChunk of chunk.getAllAsyncChunks()) {
        if (!asyncChunk.isOnlyInitial()) {
          this.mergeNonInitialChunks(asyncChunk, intoChunk, newCheckedChunks);
        }
      }
    }
  }

  static renderExtractedChunk(compilation, chunk) {
    const source = new _webpackSources.ConcatSource();

    for (const chunkModule of chunk.modulesIterable) {
      let moduleSource = chunkModule.source(compilation.dependencyTemplates, compilation.runtimeTemplate);

      // This module was concatenated by the ModuleConcatenationPlugin; because the pitching loader
      // only produces commonjs results, at least for now things we want to extract can't be in them.
      // NOTE: if ESM support is added, _this workaround will break_.
      if (moduleSource instanceof _webpackSources.ConcatSource) {
        moduleSource = null;
      }

      // Async imports (require.ensure(), import().then) are CachedSource module
      // instances caching a ReplaceSource instance, which breaks the plugin
      // because their .source() is the cached "// removed by ..." text.
      // The issue lies elsewhere, this is just a temporary fix that
      // creates a new RawSource with the extracted text. If it's
      // a CachedSource instance but there's no extracted text
      // it's "__webpack_require__();" statements. Skip it.
      if (moduleSource instanceof _webpackSources.CachedSource) {
        if (chunkModule[NS] && chunkModule[NS].content) {
          moduleSource = new _webpackSources.ConcatSource();
          if (chunkModule[NS].content.length > 1) {
            console.error(chunkModule[NS].content);
          }
          for (const content of chunkModule[NS].content) {
            moduleSource.add(new _webpackSources.RawSource(content[1]));
          }
        } else {
          moduleSource = null;
        }
      }

      if (moduleSource) {
        source.add(ExtractTextPlugin.applyAdditionalInformation(moduleSource, chunkModule.additionalInformation));
      }
    }

    return source;
  }

  extract(options) {
    if (Array.isArray(options) || (0, _helpers.isString)(options) || typeof options.options === 'object' || typeof options.query === 'object') {
      options = { use: options };
    } else {
      (0, _schemaUtils2.default)(_path2.default.resolve(__dirname, './loader.json'), options, 'Extract Text Plugin (Loader)');
    }

    let loader = options.use;
    let before = options.fallback || [];

    if ((0, _helpers.isString)(loader)) {
      loader = loader.split('!');
    }

    if ((0, _helpers.isString)(before)) {
      before = before.split('!');
    } else if (!Array.isArray(before)) {
      before = [before];
    }

    options = (0, _helpers.mergeOptions)({ omit: before.length, remove: true }, options);
    delete options.use;
    delete options.fallback;

    return [this.loader(options)].concat(before, loader).map(_helpers.getLoaderObject);
  }

  apply(compiler) {
    const { options, filename, id } = this;

    compiler.hooks.thisCompilation.tap(plugin, compilation => {
      const extractCompilation = new _ExtractTextPluginCompilation2.default();

      compilation.hooks.normalModuleLoader.tap(plugin, (loaderContext, module) => {
        loaderContext[NS] = (content, opt) => {
          if (options.disable) {
            return false;
          }

          if (!Array.isArray(content) && content != null) {
            throw new Error(`Exported value was not extracted as an array: ${JSON.stringify(content)}`);
          }

          module[NS] = {
            content,
            options: opt || {}
          };

          return options.allChunks || module[`${NS}/extract`]; // eslint-disable-line no-path-concat
        };
      });

      let extractedChunks;
      compilation.hooks.optimizeTree.tapAsync(plugin, (chunks, modules, callback) => {
        extractedChunks = chunks.map(() => new _Chunk2.default());

        chunks.forEach((chunk, i) => {
          const extractedChunk = extractedChunks[i];
          extractedChunk.index = i;
          extractedChunk.originalChunk = chunk;
          extractedChunk.name = chunk.name;
          // extractedChunk.entryModule = chunk.entryModule;

          for (const chunkGroup of chunk.groupsIterable) {
            extractedChunk.addGroup(chunkGroup);
          }
        });

        _async2.default.forEach(chunks, (chunk, chunkCallback) => {
          // eslint-disable-line no-shadow
          const extractedChunk = extractedChunks[chunks.indexOf(chunk)];
          const shouldExtract = !!(options.allChunks || (0, _helpers.isInitialOrHasNoParents)(chunk));

          _async2.default.forEach(Array.from(chunk.modulesIterable).sort(
          // NOTE: .index should be .index2 once ESM support is added
          (a, b) => a.index - b.index), (module, moduleCallback) => {
            // eslint-disable-line no-shadow
            let meta = module[NS];

            if (meta && (!meta.options.id || meta.options.id === id)) {
              const wasExtracted = Array.isArray(meta.content);

              // A stricter `shouldExtract !== wasExtracted` check to guard against cases where a previously extracted
              // module would be extracted twice. Happens when a module is a dependency of an initial and a non-initial
              // chunk. See issue #604
              if (shouldExtract && !wasExtracted) {
                module[`${NS}/extract`] = shouldExtract; // eslint-disable-line no-path-concat

                return compilation.rebuildModule(module, err => {
                  if (err) {
                    compilation.errors.push(err);

                    return moduleCallback();
                  }

                  meta = module[NS];
                  // Error out if content is not an array and is not null
                  if (!Array.isArray(meta.content) && meta.content != null) {
                    err = new Error(`${module.identifier()} doesn't export content`);
                    compilation.errors.push(err);

                    return moduleCallback();
                  }

                  if (meta.content) {
                    extractCompilation.addResultToChunk(module.identifier(), meta.content, module, extractedChunk);
                  }

                  return moduleCallback();
                });
              } else if (meta.content) {
                extractCompilation.addResultToChunk(module.identifier(), meta.content, module, extractedChunk);
              }
            }

            return moduleCallback();
          }, err => {
            if (err) {
              return chunkCallback(err);
            }

            chunkCallback();
          });
        }, err => {
          if (err) {
            return callback(err);
          }

          extractedChunks.forEach(extractedChunk => {
            if ((0, _helpers.isInitialOrHasNoParents)(extractedChunk)) {
              this.mergeNonInitialChunks(extractedChunk);
            }
          });

          extractedChunks.forEach(extractedChunk => {
            if (!(0, _helpers.isInitialOrHasNoParents)(extractedChunk)) {
              for (const chunkModule of extractedChunk.modulesIterable) {
                extractedChunk.removeModule(chunkModule);
              }
            }
          });

          compilation.hooks.optimizeExtractedChunks.call(extractedChunks);
          callback();
        });
      });

      compilation.hooks.additionalAssets.tapAsync(plugin, assetCb => {
        extractedChunks.forEach(extractedChunk => {
          if (extractedChunk.getNumberOfModules()) {
            extractedChunk.sortModules((a, b) => {
              if (!options.ignoreOrder && (0, _helpers.isInvalidOrder)(a, b)) {
                compilation.errors.push(new _OrderUndefinedError2.default(a.getOriginalModule()));
                compilation.errors.push(new _OrderUndefinedError2.default(b.getOriginalModule()));
              }

              return (0, _helpers.getOrder)(a, b);
            });

            const chunk = extractedChunk.originalChunk;
            const source = ExtractTextPlugin.renderExtractedChunk(compilation, extractedChunk);

            const getPath = format => compilation.getPath(format, {
              chunk
            }).replace(/\[(?:(\w+):)?contenthash(?::([a-z]+\d*))?(?::(\d+))?\]/gi,
            // eslint-disable-next-line func-names
            function () {
              return _loaderUtils2.default.getHashDigest(source.source(), arguments[1], arguments[2], parseInt(arguments[3], 10));
            });

            const file = (0, _helpers.isFunction)(filename) ? filename(getPath) : getPath(filename);

            compilation.assets[file] = source;
            chunk.files.push(file);
          }
        }, this);

        assetCb();
      });
    });
  }
}

ExtractTextPlugin.extract = ExtractTextPlugin.prototype.extract.bind(ExtractTextPlugin);

exports.default = ExtractTextPlugin;