var redux = require('redux');
var reduxLogger = require('redux-logger').logger;
var reducer = require('./reducers/main');

module.exports = redux.createStore(
    reducer,
    window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__(),
    redux.applyMiddleware(reduxLogger)
);