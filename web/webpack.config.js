var webpack = require('webpack');
var fs = require('fs');

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
        fs.createReadStream(__dirname + '/public/css/styles.css')
          .pipe(fs.createWriteStream(
            __dirname + '/public/dist/styles.' + 
              (process.env.BUILD === 'debug' ? 'dev' : stats.hash) + '.css'));
      });
    },
    function() {
      this.plugin('done', function(stats) {
        fs.writeFileSync(
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
