const webpack = require('webpack');
const fs = require('fs');
const glob = require('glob');

const ExtractTextPlugin = require('extract-text-webpack-plugin');

const isProduction = process.env.NODE_ENV === 'production';

module.exports = {
    devtool: isProduction ? 'sourcemap' : 'eval',
    entry: { bundle: ['babel-polyfill', './src/main.js'], styles: './src/styles.css' },
    module: {
        rules: [
            // Extract css files
            {
                test: /\.css$/,
                exclude: /^node_modules$/,
                use: ExtractTextPlugin.extract({
                    fallback: 'style-loader',
                    use: [{ loader: 'css-loader', options: { url: false } }]
                })
            },
            {
                test: [/\.js$/],
                exclude: [/node_modules/],
                loader: 'babel-loader',
                query: {
                    plugins: ['transform-runtime'],
                    presets: ['es2015']
                }
            }
        ]
    },
    plugins: [
        new webpack.optimize.UglifyJsPlugin({
            sourceMap: isProduction ? 'sourcemap' : 'eval',
            compress: {
                warnings: false,
                comparisons: false,  // don't optimize comparisons, required for MapBox to work
            },
        }),
        new ExtractTextPlugin('[name].' + (isProduction ? '[contenthash]' : 'dev') + '.css'),
        new webpack.optimize.CommonsChunkPlugin({
            name: 'vendor',
            minChunks: function (module) {
                // this assumes your vendor imports exist in the node_modules directory
                return module.context && module.context.indexOf('node_modules') !== -1;
            }
        }),
        new webpack.optimize.OccurrenceOrderPlugin(),
        function() {
            this.plugin('done', function(stats) {
            fs.writeFileSync(
                __dirname + '/public/dist/manifest.json',
                JSON.stringify(stats.toJson()));
            });
        },
        new webpack.DefinePlugin({
            'ELECTRICITYMAP_PUBLIC_TOKEN': `"${process.env.ELECTRICITYMAP_PUBLIC_TOKEN || 'development'}"`,
            'process.env': {
                'NODE_ENV': JSON.stringify(isProduction ? 'production' : 'development')
            }
        }),
    ],
    output: {
        filename: '[name].' + (isProduction ? '[chunkhash]' : 'dev') + '.js',
        path: __dirname + '/public/dist/'
    },
    // The following is required because of https://github.com/webpack-contrib/css-loader/issues/447
    node: {
      fs: "empty"
    }
};
