import { select, selectAll } from 'd3-selection';

import { history } from './helpers/router';
import { store } from './store';

export const cordovaApp = {
  // Application Constructor
  initialize() {
    this.bindEvents();
  },

  bindEvents() {
    document.addEventListener('deviceready', this.onDeviceReady, false);
    document.addEventListener('resume', this.onResume, false);
    document.addEventListener('backbutton', this.onBack, false);
  },

  onBack(e) {
    // Go to previous page if it exists, otherwise exit the app.
    if (history.length > 1) {
      history.goBack();
      e.preventDefault();
    } else {
      navigator.app.exitApp();
    }
  },

  onDeviceReady() {
    // Resize if we're on iOS
    if (cordova.platformId === 'ios') {

      const safeAreaTop = 'env(safe-area-inset-top, 20px)';
      const safeAreaBottom = 'env(safe-area-inset-bottom, 0px)';

      select('#header')
        .style('padding-top', safeAreaTop); // note: this selects nothing

      select('#mobile-header')
        .style('padding-top', safeAreaTop);

      select('.controls-container')
        .style('margin-top', safeAreaTop);

      selectAll('.flash-message .inner')
        .style('padding-top', safeAreaTop);

      select('.mapboxgl-zoom-controls')
        .style('transform', `translate(0,${safeAreaTop})`);
      select('.layer-buttons-container')
        .style('transform', `translate(0,${safeAreaTop})`);

      select('#tab')
        .style('padding-bottom', safeAreaBottom);
      select('.modal')
        .style('margin-bottom', safeAreaBottom);
    }

    codePush.sync(null, { installMode: InstallMode.ON_NEXT_RESUME });
  },

  onResume() {
    // Count as app visit
    store.dispatch({ type: 'TRACK_EVENT', payload: { eventName: 'Visit' } });
    codePush.sync(null, { installMode: InstallMode.ON_NEXT_RESUME });
  },
};
