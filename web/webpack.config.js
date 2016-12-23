var webpack = require('webpack');

module.exports = {
  devtool: (process.env.BUILD === 'debug' ? 'eval' : 'sourcemap'),
  entry: './app/main.js',
  plugins: [
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
    filename: 'bundle.' + (process.env.BUILD === 'debug' ? 'dev' : '[hash]') + '.js',
    path: __dirname + '/public/dist/'
  },
  resolve: {
    moduleDirectories: ['node_modules']
  }
};
