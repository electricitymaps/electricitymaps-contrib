var CleanWebpackPlugin = require('clean-webpack-plugin');
var webpack = require('webpack');

module.exports = {
  devtool: 'sourcemap',
  entry: './app/main.js',
  plugins: [
    new CleanWebpackPlugin(['public/dist']),
    new webpack.optimize.DedupePlugin(),
    new webpack.optimize.OccurenceOrderPlugin(),
    new webpack.optimize.UglifyJsPlugin({
      compress: {
          warnings: false
      }
    }),
    function() {
      this.plugin('done', function(stats) {
        require('fs').writeFileSync(
          __dirname + '/public/dist/manifest.json',
          JSON.stringify(stats.toJson()));
      });
    }
  ],
  output: {
    filename: 'bundle.[hash].js',
    path: __dirname + '/public/dist/'
  }
};
