window.StackTrace = require('stacktrace-js');
const { StackdriverErrorReporter } = require('stackdriver-errors-js');
const store = require('../../store');

class StackdriverThirdParty {
  constructor() {
    if (store.getState().application.isProduction) {
      this.errorHandler = new StackdriverErrorReporter();
      this.errorHandler.start({
        key: 'AIzaSyDSbdOoEho3cr7m7FDtcrReFeeXgLC9hEg',
        projectId: 'tmrow-152415',
        service: 'electricitymap-public_web',
        version: store.getState().application.bundleHash,
        reportUncaughtExceptions: true,    // (optional) Set to false to stop reporting unhandled exceptions.
        // disabled: true                  // (optional) Set to true to not report errors when calling report(), this can be used when developping locally.
        // context: {user: 'user1'}        // (optional) You can set the user later using setUser()
      });
    } else {
      console.warn('Stackdriver disabled in development mode');
    }
  }

  track(event, data) {} // no-op

  report() {
    this.errorHandler.report(...arguments);
  }
}

module.exports = new StackdriverThirdParty();
