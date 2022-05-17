import { select } from 'd3-selection';

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
    console.log('Cordova: onDeviceReady'); // eslint-disable-line no-console
    // Resize if we're on iOS
    if (cordova.platformId === 'ios') {
      const styles = function (top, bottom) {
        return `
        /* TODO: this selects nothing, header on iPad still overlaps with the status bar */
        #header {
          padding-top: ${top};
        }

        #mobile-header {
          padding-top: ${top};
        }
        .controls-container {
          margin-top: ${top};
        }
        .flash-message .inner {
          padding-top: ${top};
        }
        .mapboxgl-zoom-controls {
          transform: translate(0, ${top});
        }
        .layer-buttons-container {
          /* Note: Don't use transform here, as it breaks child position fixed elements (lang. selector) */
          margin-top: ${top};
        }
        .language-select-container {
          padding-top: ${top};
        }

        #tab {
          padding-bottom: ${bottom};
        }
        .modal {
          padding-bottom: ${bottom};
        }
        `;
      };

      select('head').append('style').text(`
            /* Fixes current issue on iOS where there's a gap at bottom.
            See https://github.com/apache/cordova-plugin-wkwebview-engine/issues/172
            */
            html {height: 100vh;}
            /* iOS 10 */
            ${styles('20px', '0px')}
            /* iOS 11.0 */
            @supports(padding-top: constant(safe-area-inset-top)) {
              ${styles('constant(safe-area-inset-top, 20px)', 'constant(safe-area-inset-bottom, 0px)')}
            }
            /* iOS 11+ */
            @supports(padding-top: env(safe-area-inset-top)) {
              ${styles('env(safe-area-inset-top, 20px)', 'env(safe-area-inset-bottom, 0px)')}
            }
          `);
    }

    codePush.sync(null, { installMode: InstallMode.ON_NEXT_RESUME });
  },

  onResume() {
    // Count as app visit
    store.dispatch({ type: 'TRACK_EVENT', payload: { eventName: 'Visit' } });
    codePush.sync(null, { installMode: InstallMode.ON_NEXT_RESUME });
  },
};
