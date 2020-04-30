import { select } from 'd3-selection';

import thirdPartyServices from './services/thirdparty';
import { history, navigateTo, getCurrentPage } from './helpers/router';

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
    if (['zone', 'faq'].includes(getCurrentPage())) {
      navigateTo({ pathname: '/map', search: history.location.search });
      e.preventDefault();
    } else {
      navigator.app.exitApp();
    }
  },

  onDeviceReady() {
    // Resize if we're on iOS
    if (cordova.platformId === 'ios') {
      // TODO(olc): What about Xr and Xs?
      const extraPadding = (device.model === 'iPhone10,3' || device.model === 'iPhone10,6')
        ? 30
        : 20;
      select('#header')
        .style('padding-top', `${extraPadding}px`);
      select('#mobile-header')
        .style('padding-top', `${extraPadding}px`);

      select('.controls-container')
        .style('margin-top', `${extraPadding}px`);

      select('.flash-message .inner')
        .style('padding-top', `${extraPadding}px`);

      select('.mapboxgl-zoom-controls')
        .style('transform', `translate(0,${extraPadding}px)`);
      select('.layer-buttons-container')
        .style('transform', `translate(0,${extraPadding}px)`);
    }

    codePush.sync(null, { installMode: InstallMode.ON_NEXT_RESUME });
  },

  onResume() {
    // Count as app visit
    thirdPartyServices.trackWithCurrentApplicationState('Visit');
    codePush.sync(null, { installMode: InstallMode.ON_NEXT_RESUME });
  },
};
