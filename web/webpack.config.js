var webpack = require('webpack');

module.exports = {
  devtool: 'sourcemap',
  entry: './app/main.js',
  output: {
    filename: 'bundle.js',
    path: __dirname + '/public/dist/'
  }
};
