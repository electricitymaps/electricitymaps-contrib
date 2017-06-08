var webpack = require('webpack');
var fs = require('fs');
var glob = require('glob');

module.exports = {
  devtool: (process.env.NODE_ENV === 'production' ? 'sourcemap' : 'eval'),
  entry: './app/main.js',
  plugins: [
    function() {
      this.plugin('emit', function(compilation, callback) {
        compilation.fileDependencies.push(__dirname + '/public/css/styles.css');
        glob(__dirname + '/../config/**/*.js', function(err, files) {
          files.forEach(function(f) { compilation.fileDependencies.push(f); });
        })
        callback();
      });
    },
    new webpack.optimize.OccurrenceOrderPlugin(),
    function() {
      this.plugin('done', function(stats) {
        fs.createReadStream(__dirname + '/public/css/styles.css')
          .pipe(fs.createWriteStream(
            __dirname + '/public/dist/styles.' + 
              (process.env.NODE_ENV === 'production' ? stats.hash : 'dev') + '.css'));
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
    filename: 'bundle.' + (process.env.NODE_ENV === 'production' ? '[hash]' : 'dev') + '.js',
    path: __dirname + '/public/dist/'
  }
};
