const webpack = require('webpack');
const fs = require('fs');
const autoprefixer = require('autoprefixer');

const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const OptimizeCssAssetsPlugin = require('optimize-css-assets-webpack-plugin');

const isProduction = process.env.NODE_ENV === 'production';
const { languageNames } = require('./locales-config.json');

const { version } = require('./package.json');

/*
  Note exporting a config per language makes the build slower.
  Sequential builds are faster (using jq and `--config-name`)
*/
module.exports = Object.keys(languageNames).map(locale => ({
  name: locale,
  devtool: isProduction ? 'sourcemap' : 'eval',
  entry: { bundle: ['@babel-polyfill', './src/main.js'], styles: './src/scss/styles.scss' },
  module: {
    noParse: /(mapbox-gl)\.js$/,
    rules: [
      // Extract css files
      {
        test: /\.(sa|sc|c)ss$/,
        exclude: /^node_modules$/,
        use: [
          MiniCssExtractPlugin.loader,
          { loader: 'css-loader', options: { url: false } },
          { loader: 'postcss-loader', options: { plugins: [autoprefixer()] } },
          { loader: 'sass-loader', options: { sourceMap: true } },
        ],
      },
      {
        test: [/\.js$/],
        exclude: [/node_modules/],
        loader: 'babel-loader',
        query: {
          presets: ['@babel/preset-env', '@babel/preset-react'],
          cacheDirectory: true, // cache results for subsequent builds
        },
      },
    ],
  },
  plugins: [
    new webpack.ContextReplacementPlugin(/moment[/\\]locale$/, new RegExp(`/${locale}/`)),
    // Only include current locale + en
    new webpack.ContextReplacementPlugin(/locales/, new RegExp(`/${locale}|en/`)),
    new MiniCssExtractPlugin(`[name].${isProduction ? '[hash]' : 'dev'}.css`),
    new OptimizeCssAssetsPlugin(),
    new webpack.optimize.OccurrenceOrderPlugin(),
    function () {
      this.plugin('done', (stats) => {
        fs.writeFileSync(
          `${__dirname}/public/dist/manifest_${locale}.json`,
          JSON.stringify(stats.toJson())
        );
      });
    },
    new webpack.DefinePlugin({
      ELECTRICITYMAP_PUBLIC_TOKEN: `"${process.env.ELECTRICITYMAP_PUBLIC_TOKEN || 'development'}"`,
      VERSION: JSON.stringify(version),
      'process.env': {
        NODE_ENV: JSON.stringify(isProduction ? 'production' : 'development'),
      },
    }),
  ],
  optimization: {
    splitChunks: {
      cacheGroups: {
        commons: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendor',
          chunks: 'all',
        },
      },
    },
  },
  output: {
    // filename affects styles.js and bundle.js
    filename: chunkData => (['styles'].includes(chunkData.chunk.name)
      ? `[name].${isProduction ? '[chunkhash]' : 'dev'}.js`
      : `[name].${isProduction ? '[chunkhash]' : 'dev'}.${locale}.js`),
    // chunkFilename affects `vendor.js`
    chunkFilename: `[name].${isProduction ? '[chunkhash]' : 'dev'}.js`,
    path: `${__dirname}/public/dist`,
    pathinfo: false,
  },
  // The following is required because of https://github.com/webpack-contrib/css-loader/issues/447
  node: {
    fs: 'empty',
  },
}));
