const redux = require('redux');
const reduxLogger = require('redux-logger').logger;
const reducer = require('./reducers/main');

module.exports = redux.createStore(
  reducer,
  window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__(),
  redux.applyMiddleware(reduxLogger),
);
