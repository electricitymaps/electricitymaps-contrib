var webpack = require('webpack');
var fs = require('fs');
var glob = require('glob');

module.exports = {
  devtool: (process.env.BUILD === 'debug' ? 'eval' : 'sourcemap'),
  entry: './app/main.js',
  plugins: [
    function() {
      this.plugin('emit', function(compilation, callback) {
        compilation.fileDependencies.push(__dirname + '/public/css/styles.css');
        glob(__dirname + '/../shared/**/*.js', function(err, files) {
          files.forEach(function(f) { compilation.fileDependencies.push(f); });
        })
        callback();
      });
    },
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
