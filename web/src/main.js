'use strict';

import CountryMap from './components/map';
// see https://stackoverflow.com/questions/36887428/d3-event-is-null-in-a-reactjs-d3js-component
import { event as currentEvent } from 'd3-selection';

// Libraries
const d3 = Object.assign(
  {},
  require('d3-array'),
  require('d3-collection'),
  require('d3-interpolate'),
  require('d3-queue'),
  require('d3-request'),
  require('d3-selection'),
  require('d3-scale'),
);

const Cookies = require('js-cookie');
const moment = require('moment');

const thirdPartyServices = require('./services/thirdparty');
const { dispatch, getState, observe } = require('./store');

const AreaGraph = require('./components/areagraph');
const LineGraph = require('./components/linegraph');
const CountryTable = require('./components/countrytable');
const HorizontalColorbar = require('./components/horizontalcolorbar');
const Tooltip = require('./components/tooltip');

const CountryTopos = require('./countrytopos');
const DataService = require('./dataservice');

const ExchangeLayer = require('./components/layers/exchange');
const SolarLayer = require('./components/layers/solar');
const WindLayer = require('./components/layers/wind');

const flags = require('./flags');
const LoadingService = require('./services/loadingservice');

const HistoryState = require('./helpers/historystate');
const grib = require('./helpers/grib');
const translation = require('./translation');
const tooltipHelper = require('./helpers/tooltip');

const { getSymbolFromCurrency } = require('currency-symbol-map');

// Configs
const exchangesConfig = require('../../config/exchanges.json');
const zonesConfig = require('../../config/zones.json');

// Timing
if (thirdPartyServices._ga) {
  thirdPartyServices._ga.timingMark('start_executing_js');
}

// Constants
const REFRESH_TIME_MINUTES = 5;

// Set state depending on URL params
HistoryState.parseInitial(window.location.search);
const applicationState = HistoryState.getStateFromHistory();
Object.keys(applicationState).forEach((k) => {
  dispatchApplication(k, applicationState[k]);
});

// TODO(olc) move those to redux state
let currentMoment;
let previousShowPageState;
let mapDraggedSinceStart = false;

const REMOTE_ENDPOINT = 'https://api.electricitymap.org';
const LOCAL_ENDPOINT = 'http://localhost:9000';
const ENDPOINT = getState().application.useRemoteEndpoint ?
  REMOTE_ENDPOINT : LOCAL_ENDPOINT;

function dispatchApplication(key, value) {
  return dispatch({
    payload: { key, value },
    type: 'APPLICATION_STATE_UPDATE',
  });
}

// Initialise mobile app (cordova)
const app = {
  // Application Constructor
  initialize: function() {
    this.bindEvents();
  },

  bindEvents: function() {
    document.addEventListener('deviceready', this.onDeviceReady, false);
    document.addEventListener('resume', this.onResume, false);
    document.addEventListener('backbutton', this.onBack, false);
  },

  onBack: function(e) {
    if (getState().application.showPageState !== 'map') {
      dispatchApplication('selectedCountryCode', undefined);
      dispatchApplication('showPageState', previousShowPageState || 'map');
      e.preventDefault();
    } else {
      navigator.app.exitApp();
    }
  },

  onDeviceReady: function() {
    // Resize if we're on iOS
    if (cordova.platformId === 'ios') {
      d3.select('#header')
        .style('padding-top', '20px');
      if (typeof countryMap !== 'undefined') {
        countryMap.map.resize();
      }
    }
    codePush.sync(null, { installMode: InstallMode.ON_NEXT_RESUME });
    universalLinks.subscribe(null, (eventData) => {
      HistoryState.parseInitial(eventData.url.split('?')[1] || eventData.url);
      // In principle we should only do the rest of the app loading
      // after this point, instead of dispating a new event
      const applicationState = HistoryState.getStateFromHistory();
      Object.keys(applicationState).forEach((k) => {
        dispatchApplication(k, applicationState[k]);
      });
    });
  },

  onResume: function() {
    // Count a pageview
    const params = getState().application;
    params.bundleVersion = params.bundleHash;
    params.embeddedUri = params.isEmbedded ? document.referrer : null;
    thirdPartyServices.track('Visit', params);
    codePush.sync(null, { installMode: InstallMode.ON_NEXT_RESUME });
  },
};
app.initialize();

function catchError(e) {
  console.error('Error Caught! ' + e);
  thirdPartyServices.opbeat('captureException', e);
  thirdPartyServices.ga('event', 'exception', { description: e, fatal: false });
  const params = getState().application;
  params.name = e.name;
  params.stack = e.stack;
  thirdPartyServices.track('error', params);
}

// Set proper locale
moment.locale(getState().application.locale.toLowerCase());

// Analytics
(() => {
  const params = getState().application;
  params.bundleVersion = params.bundleHash;
  params.embeddedUri = params.isEmbedded ? document.referrer : null;
  thirdPartyServices.track('Visit', params);
})();

// Display embedded warning
// d3.select('#embedded-error').style('display', isEmbedded ? 'block' : 'none');

// Prepare co2 scale
const maxCo2 = 800;
let co2color;
let co2Colorbars;
function updateCo2Scale() {
  if (getState().application.colorBlindModeEnabled) {
    co2color = d3.scaleSequential(d3.interpolateMagma)
      .domain([2000, 0]);
  } else {
    co2color = d3.scaleLinear()
      .domain([0, 375, 725, 800])
      .range(['green', 'orange', 'rgb(26,13,0)']);
  }

  co2color.clamp(true);
  co2Colorbars = co2Colorbars || [];
  co2Colorbars.push(new HorizontalColorbar('#layer-toggles .co2-colorbar', co2color)
    .markerColor('white')
    .domain([0, maxCo2])
    .render());
  co2Colorbars.push(new HorizontalColorbar('.co2-floating-legend .co2-colorbar', co2color, null, [0, 400, 800])
    .markerColor('white')
    .domain([0, maxCo2])
    .render());
  if (typeof countryMap !== 'undefined') countryMap.setCo2color(co2color);
  if (countryTable) countryTable.co2color(co2color).render();
  if (countryHistoryCarbonGraph) countryHistoryCarbonGraph.yColorScale(co2color);
  if (countryHistoryMixGraph) countryHistoryMixGraph.co2color(co2color);
  if (countryListSelector)
    countryListSelector
      .select('div.emission-rect')
      .style('background-color', d => {
        return d.co2intensity ? co2color(d.co2intensity) : 'gray';
      });
}
d3.select('#checkbox-colorblind').node().checked = getState().application.colorBlindModeEnabled;
d3.select('#checkbox-colorblind').on('change', () => {
  dispatchApplication('colorBlindModeEnabled', !getState().application.colorBlindModeEnabled);
});
updateCo2Scale();

const maxWind = 15;
const windColor = d3.scaleLinear()
  .domain(d3.range(10).map(i => d3.interpolate(0, maxWind)(i / (10 - 1))))
  .range([
    "rgba(0,   255, 255, 1.0)",
    "rgba(100, 240, 255, 1.0)",
    "rgba(135, 225, 255, 1.0)",
    "rgba(160, 208, 255, 1.0)",
    "rgba(181, 192, 255, 1.0)",
    "rgba(198, 173, 255, 1.0)",
    "rgba(212, 155, 255, 1.0)",
    "rgba(225, 133, 255, 1.0)",
    "rgba(236, 109, 255, 1.0)",
    "rgba(255,  30, 219, 1.0)",
    ])
  .clamp(true);
// ** Solar Scale **
const maxSolarDSWRF = 1000;
const minDayDSWRF = 0;
// const nightOpacity = 0.8;
const minSolarDayOpacity = 0.6;
const maxSolarDayOpacity = 0.0;
const solarDomain = d3.range(10).map(i => d3.interpolate(minDayDSWRF, maxSolarDSWRF)(i / (10 - 1)));
const solarRange = d3.range(10).map((i) => {
  const c = Math.round(d3.interpolate(0, 0)(i / (10 - 1)));
  const a = d3.interpolate(minSolarDayOpacity, maxSolarDayOpacity)(i / (10 - 1));
  return 'rgba(' + c + ', ' + c + ', ' + c + ', ' + a + ')';
});
// Insert the night (DWSWRF \in [0, minDayDSWRF]) domain
// solarDomain.splice(0, 0, 0);
// solarRange.splice(0, 0, 'rgba(0, 0, 0, ' + nightOpacity + ')');
// Create scale
const solarColor = d3.scaleLinear()
  .domain(solarDomain)
  .range(solarRange)
  .clamp(true);

// Production/imports-exports mode
const modeColor = {
  'wind': '#74cdb9',
  'solar': '#f27406',
  'hydro': '#2772b2',
  'hydro storage': '#0052cc',
  'battery': 'lightgray',
  'biomass': '#166a57',
  'geothermal': 'yellow',
  'nuclear': '#AEB800',
  'gas': '#bb2f51',
  'coal': '#ac8c35',
  'oil': '#867d66',
  'unknown': 'lightgray',
};
const modeOrder = [
  'wind',
  'solar',
  'hydro',
  'hydro storage',
  'battery storage',
  'geothermal',
  'biomass',
  'nuclear',
  'gas',
  'coal',
  'oil',
  'unknown',
];

// Set up objects
let exchangeLayer = null;
LoadingService.startLoading('#loading');
LoadingService.startLoading('#small-loading');
let countryMap;
let windLayer;
let solarLayer;
try {
  countryMap = new CountryMap('zones')
    .setCo2color(co2color)
    .onDragEnd(() => {
      if (!mapDraggedSinceStart) { mapDraggedSinceStart = true; }
    })
    .onMapLoaded((map) => {
      // Nest the exchange layer inside
      const el = document.createElement('div');
      el.id = 'arrows-layer';
      map.map.getCanvas()
        .parentNode
        .appendChild(el);
      // Create exchange layer as a result
      exchangeLayer = new ExchangeLayer('arrows-layer', countryMap)
        .onExchangeMouseOver((d) => {
          tooltipHelper.showMapExchange(exchangeTooltip, d, co2color, co2Colorbars);
        })
        .onExchangeMouseMove(() => {
          exchangeTooltip.update(currentEvent.clientX, currentEvent.clientY);
        })
        .onExchangeMouseOut((d) => {
          if (d.co2intensity && co2Colorbars)
            co2Colorbars.forEach((c) => { c.currentMarker(undefined); });
          exchangeTooltip.hide();
        })
        .onExchangeClick((d) => {
          console.log(d);
        })
        .setData(Object.values(exchanges))
        .render();
      LoadingService.stopLoading('#loading');
      LoadingService.stopLoading('#small-loading');
      if (thirdPartyServices._ga) {
        thirdPartyServices._ga.timingMark('map_loaded');
      }
    });
  windLayer = new WindLayer('wind', countryMap);
  solarLayer = new SolarLayer('solar', countryMap);
  dispatchApplication('webglsupported', true);
} catch (e) {
  if (e === 'WebGL not supported') {
    // Set mobile mode, and disable maps
    dispatchApplication('webglsupported', false);
    dispatchApplication('showPageState', 'highscore');
    document.getElementById('tab').className = 'nomap';
    document.getElementById('layer-toggles').style.display = 'none';

    // Loading is finished
    LoadingService.stopLoading('#loading');
    LoadingService.stopLoading('#small-loading');
  } else {
    throw e;
  }
}

const countryTableExchangeTooltip = new Tooltip('#countrypanel-exchange-tooltip');
const countryTableProductionTooltip = new Tooltip('#countrypanel-production-tooltip');
const countryTooltip = new Tooltip('#country-tooltip');
const exchangeTooltip = new Tooltip('#exchange-tooltip');
const priceTooltip = new Tooltip('#price-tooltip');
const countryTable = new CountryTable('.country-table', modeColor, modeOrder)
  .co2color(co2color)
  .onExchangeMouseMove(() => {
    countryTableExchangeTooltip.update(currentEvent.clientX, currentEvent.clientY);
  })
  .onExchangeMouseOver((d, country, displayByEmissions) => {
    tooltipHelper.showExchange(
      countryTableExchangeTooltip,
      d, country, displayByEmissions,
      co2color, co2Colorbars);
  })
  .onExchangeMouseOut(d => {
    if (co2Colorbars) co2Colorbars.forEach(d => { d.currentMarker(undefined) });
    countryTableExchangeTooltip.hide()
  })
  .onProductionMouseOver((mode, country, displayByEmissions) => {
    tooltipHelper.showProduction(
      countryTableProductionTooltip,
      mode, country, displayByEmissions,
      co2color, co2Colorbars);
  })
  .onProductionMouseMove(d => {
    countryTableProductionTooltip.update(currentEvent.clientX, currentEvent.clientY)
  })
  .onProductionMouseOut(d => {
    if (co2Colorbars) co2Colorbars.forEach(d => { d.currentMarker(undefined) });
    countryTableProductionTooltip.hide();
  });

let countryHistoryCarbonGraph = new LineGraph('#country-history-carbon',
  d => moment(d.stateDatetime).toDate(),
  d => d.co2intensity,
  d => d.co2intensity != null)
  .yColorScale(co2color)
  .gradient(true);
const countryHistoryPricesGraph = new LineGraph('#country-history-prices',
  d => moment(d.stateDatetime).toDate(),
  d => (d.price || {}).value,
  d => d.price && d.price.value != null)
  .gradient(false);
let countryHistoryMixGraph = new AreaGraph('#country-history-mix', modeColor, modeOrder)
  .co2color(co2color)
  .onLayerMouseOver((mode, countryData, i) => {
    const isExchange = modeOrder.indexOf(mode) === -1;
    const fun = isExchange ?
      tooltipHelper.showExchange : tooltipHelper.showProduction;
    const ttp = isExchange ?
      countryTableExchangeTooltip : countryTableProductionTooltip;
    fun(ttp,
      mode, countryData, tableDisplayEmissions,
      co2color, co2Colorbars);
    dispatch({
      type: 'SELECT_DATA',
      payload: { countryData, index: i },
    });
  })
  .onLayerMouseMove((mode, countryData, i) => {
    const isExchange = modeOrder.indexOf(mode) === -1;
    const fun = isExchange ?
      tooltipHelper.showExchange : tooltipHelper.showProduction;
    const ttp = isExchange ?
      countryTableExchangeTooltip : countryTableProductionTooltip;
    ttp.update(
      currentEvent.clientX - 7,
      countryHistoryMixGraph.rootElement.node().getBoundingClientRect().top + 7)
    fun(ttp,
      mode, countryData, tableDisplayEmissions,
      co2color, co2Colorbars)
    dispatch({
      type: 'SELECT_DATA',
      payload: { countryData, index: i },
    });
  })
  .onLayerMouseOut((mode, countryData, i) => {
    if (co2Colorbars) co2Colorbars.forEach((d) => { d.currentMarker(undefined); });
    const isExchange = modeOrder.indexOf(mode) === -1;
    const ttp = isExchange ?
      countryTableExchangeTooltip : countryTableProductionTooltip;
    ttp.hide();
  });

const windColorbar = new HorizontalColorbar('.wind-colorbar', windColor)
  .markerColor('black');
const solarColorbarColor = d3.scaleLinear()
  .domain([0, 0.5 * maxSolarDSWRF, maxSolarDSWRF])
  .range(['black', 'white', 'gold']);
const solarColorbar = new HorizontalColorbar('.solar-colorbar', solarColorbarColor)
  .markerColor('red');

let tableDisplayEmissions = countryTable.displayByEmissions();
countryHistoryMixGraph
  .displayByEmissions(tableDisplayEmissions);
d3.select('.country-show-emissions-wrap a#emissions')
  .classed('selected', tableDisplayEmissions);
d3.select('.country-show-emissions-wrap a#production')
  .classed('selected', !tableDisplayEmissions);

window.toggleSource = (state) => {
  if (state === undefined)
    state = !tableDisplayEmissions;
  tableDisplayEmissions = state;
  thirdPartyServices.track(
    tableDisplayEmissions ? 'switchToCountryEmissions' : 'switchToCountryProduction',
    { countryCode: countryTable.data().countryCode });
  countryTable
    .displayByEmissions(tableDisplayEmissions);
  countryHistoryMixGraph
    .displayByEmissions(tableDisplayEmissions);
  d3.select('.country-show-emissions-wrap a#emissions')
    .classed('selected', tableDisplayEmissions);
  d3.select('.country-show-emissions-wrap a#production')
    .classed('selected', !tableDisplayEmissions);
};

// Prepare data
const countries = CountryTopos.addCountryTopos({});
// Validate selected country
if (d3.keys(countries).indexOf(getState().application.selectedCountryCode) === -1) {
  dispatchApplication('selectedCountryCode', undefined);
  if (getState().application.showPageState === 'country') {
    dispatchApplication('showPageState', 'map');
  }
}
// Assign data
if (typeof countryMap !== 'undefined') { countryMap.setData(d3.values(countries)); }
// Add configurations
d3.entries(zonesConfig).forEach(d => {
  const zone = countries[d.key];
  if (!zone) {
    console.warn('Zone ' + d.key + ' from configuration is not found. Ignoring..');
    return;
  }
  // copy each zone attributes ("capacity", "contributors"...) into global object
  d3.entries(d.value).forEach((o) => { zone[o.key] = o.value; });
  zone.shortname = translation.translate('zoneShortName.' + d.key);
});
// Add id to each zone
d3.entries(countries).forEach(d => {
  let zone = countries[d.key];
  zone.countryCode = d.key; // TODO: Rename to zoneId
});
let exchanges = exchangesConfig;
d3.entries(exchanges).forEach((entry) => {
  entry.value.countryCodes = entry.key.split('->').sort();
  if (entry.key.split('->')[0] != entry.value.countryCodes[0])
    console.error('Exchange sorted key pair ' + entry.key + ' is not sorted alphabetically');
});

let wind, solar, callerLocation;

let histories = {};

function selectCountry(countryCode, notrack) {
  if (!countries) { return; }
  if (countryCode && countries[countryCode]) {
    // Selected
    if (!notrack) {
      const params = getState().application;
      params.bundleVersion = params.bundleHash;
      params.embeddedUri = params.isEmbedded ? document.referrer : null;
      thirdPartyServices.track('pageview', params);
      thirdPartyServices.track('countryClick', { countryCode });
    }
    countryTable
      .powerScaleDomain(null) // Always reset scale if click on a new country
      .co2ScaleDomain(null)
      .exchangeKeys(null); // Always reset exchange keys
    dispatch({
      type: 'ZONE_DATA',
      payload: countries[countryCode],
    });

    const maxStorageCapacity = countries[countryCode].maxStorageCapacity;


    function updateGraph(countryHistory) {
      // No export capacities are not always defined, and they are thus
      // varying the scale.
      // Here's a hack to fix it.
      let lo = d3.min(countryHistory, d => {
        return Math.min(
          -d.maxStorageCapacity || -maxStorageCapacity || 0,
          -d.maxStorage || 0,
          -d.maxExport || 0,
          -d.maxExportCapacity || 0);
      });
      let hi = d3.max(countryHistory, d => {
        return Math.max(
          d.maxCapacity || 0,
          d.maxProduction || 0,
          d.maxImport || 0,
          d.maxImportCapacity || 0,
          d.maxDischarge || 0,
          d.maxStorageCapacity || maxStorageCapacity || 0);
      });
      // TODO(olc): do those aggregates server-side
      let lo_emission = d3.min(countryHistory, d => {
        return Math.min(
          // Max export
          d3.min(d3.entries(d.exchange), function(o) {
            return Math.min(o.value, 0) * d.exchangeCo2Intensities[o.key] / 1e3 / 60.0
          })
          // Max storage
          // ?
          );
      });
      let hi_emission = d3.max(countryHistory, d => {
        return Math.max(
          // Max import
          d3.max(d3.entries(d.exchange), function(o) {
            return Math.max(o.value, 0) * d.exchangeCo2Intensities[o.key] / 1e3 / 60.0
          }),
          // Max production
          d3.max(d3.entries(d.production), function(o) {
            return Math.max(o.value, 0) * d.productionCo2Intensities[o.key] / 1e3 / 60.0
          })
        );
      });

      // Figure out the highest CO2 emissions
      let hi_co2 = d3.max(countryHistory, d => {
        return d.co2intensity;
      });
      countryHistoryCarbonGraph.y.domain([0, 1.1 * hi_co2]);

      // Create price color scale
      let priceExtent = d3.extent(countryHistory, d => {
        return (d.price || {}).value;
      });
      countryHistoryPricesGraph.y.domain(
        [Math.min(0, priceExtent[0]), 1.1 * priceExtent[1]]);

      countryHistoryCarbonGraph
        .data(countryHistory);
      countryHistoryPricesGraph
        .yColorScale(d3.scaleLinear()
          .domain(countryHistoryPricesGraph.y.domain())
          .range(['yellow', 'red']))
        .data(countryHistory);
      countryHistoryMixGraph
        .data(countryHistory);

      // Update country table with all possible exchanges
      countryTable
        .exchangeKeys(
          countryHistoryMixGraph.exchangeKeysSet.values())
        .render();

      let firstDatetime = countryHistory[0] &&
        moment(countryHistory[0].stateDatetime).toDate();
      [countryHistoryCarbonGraph, countryHistoryPricesGraph, countryHistoryMixGraph].forEach((g) => {
        if (currentMoment && firstDatetime) {
          g.xDomain([firstDatetime, currentMoment.toDate()]);
        }
        g
          .onMouseMove((d, i) => {
            if (!d) return;
            // In case of missing data
            if (!d.countryCode) {
              d.countryCode = countryCode;
            }
            countryTable
              .powerScaleDomain([lo, hi])
              .co2ScaleDomain([lo_emission, hi_emission]);

            if (g === countryHistoryCarbonGraph) {
              tooltipHelper.showMapCountry(countryTooltip, d, co2color, co2Colorbars);
              countryTooltip.update(
                currentEvent.clientX - 7,
                g.rootElement.node().getBoundingClientRect().top + 7);
            } else if (g === countryHistoryPricesGraph) {
              const tooltip = d3.select(priceTooltip._selector);
              tooltip.select('.value').html((d.price || {}).value || '?');
              tooltip.select('.currency').html(getSymbolFromCurrency((d.price || {}).currency) || '?');
              priceTooltip.show();
              priceTooltip.update(
                currentEvent.clientX - 7,
                g.rootElement.node().getBoundingClientRect().top + 7);
            }

            dispatch({
              type: 'SELECT_DATA',
              payload: { countryData: d, index: i },
            });
          })
          .onMouseOut((d, i) => {
            countryTable
              .powerScaleDomain(null)
              .co2ScaleDomain(null);

            if (g === countryHistoryCarbonGraph) {
              countryTooltip.hide();
            } else if (g === countryHistoryMixGraph) {
              countryTableProductionTooltip.hide();
              countryTableExchangeTooltip.hide();
            } else if (g === countryHistoryPricesGraph) {
              priceTooltip.hide();
            }

            dispatch({
              type: 'SELECT_DATA',
              payload: { countryData: countries[countryCode], index: undefined }
            });
          })
          .render();
      });
    }

    // Load graph
    if (getState().application.customDate) {
      console.error('Can\'t fetch history when a custom date is provided!');
    }
    else if (!histories[countryCode]) {
      LoadingService.startLoading('.country-history .loading');
      DataService.fetchHistory(ENDPOINT, countryCode, function(err, obj) {
        LoadingService.stopLoading('.country-history .loading');
        if (err) console.error(err);
        if (!obj || !obj.data) console.warn('Empty history received for ' + countryCode);
        if (err || !obj || !obj.data) {
          updateGraph([]);
          return;
        }

        // Add capacities
        if ((zonesConfig[countryCode] || {}).capacity) {
          let maxCapacity = d3.max(d3.values(
            zonesConfig[countryCode].capacity));
          obj.data.forEach(d => {
            d.capacity = zonesConfig[countryCode].capacity;
            d.maxCapacity = maxCapacity;
          });
        }

        // Save to local cache
        histories[countryCode] = obj.data;

        // Show
        updateGraph(histories[countryCode]);
      });
    } else {
      updateGraph(histories[countryCode]);
    }

    // Update contributors
    let selector = d3.selectAll('.contributors').selectAll('a')
      .data((zonesConfig[countryCode] || {}).contributors || []);
    let enterA = selector.enter().append('a')
      .attr('target', '_blank');
    let enterImg = enterA.append('img');
    enterA.merge(selector)
      .attr('href', d => d);
    enterImg.merge(selector.select('img'))
      .attr('src', d => d + '.png');
    selector.exit().remove();
  }
}
// Bind
if (typeof countryMap !== 'undefined') {
  countryMap
    .onSeaClick(() => {
      dispatchApplication('selectedCountryCode', undefined);
      dispatchApplication('showPageState', 'map');
    })
    .onCountryClick((d) => {
      dispatchApplication('selectedCountryCode', d.countryCode);
      dispatchApplication('showPageState', 'country');
    });
}
d3.selectAll('#left-panel-country-back')
  .on('click', () => {
    dispatchApplication('selectedCountryCode', undefined);
    dispatchApplication('showPageState', previousShowPageState || 'map');
  });
d3.selectAll('#left-panel-highscore-back')
  .on('click', () => { dispatchApplication('showPageState', 'map'); }); // only triggered on large screens
d3.selectAll('.highscore-button').on('click', () => {
  dispatchApplication('showPageState', 'highscore');
});
d3.selectAll('.map-button').on('click', () => { dispatchApplication('showPageState', 'map'); });
d3.selectAll('.info-button').on('click', () => { dispatchApplication('showPageState', 'info'); });

function showPage(pageName) {

  if (pageName === undefined)
    pageName = 'map';

  dispatchApplication('showPageState', pageName);

  if (getState().application.showPageState !== 'country')
    previousShowPageState = getState().application.showPageState;

  // Hide all panels - we will show only the ones we need
  d3.selectAll('.left-panel > div').style('display', 'none');
  d3.selectAll('.left-panel .left-panel-social').style('display', undefined);

  // Hide info screen on large screen only
  d3.selectAll('.left-panel .left-panel-info')
    // Only show on info or map
    .style('display', (pageName == 'info' || pageName == 'map') ? undefined : 'none')
    // but hide for small screens on all but info
    .classed('large-screen-visible', pageName != 'info');

  // Hide map on small screens
  // It's important we show the map before rendering it to make sure
  // sizes are set properly
  d3.selectAll('#map-container').classed('large-screen-visible', pageName != 'map');

  if (pageName === 'map') {
    d3.select('.left-panel').classed('large-screen-visible', true);
    selectCountry(undefined);
    renderMap();
    if (getState().application.windEnabled && typeof windLayer !== 'undefined') { windLayer.show(); }
    if (getState().application.solarEnabled && typeof solarLayer !== 'undefined') { solarLayer.show(); }
    if (co2Colorbars) co2Colorbars.forEach(d => { d.render() });
    if (getState().application.windEnabled && windColorbar) windColorbar.render();
    if (getState().application.solarEnabled && solarColorbar) solarColorbar.render();
  }
  else {
    d3.select('.left-panel').classed('large-screen-visible', false);
    d3.selectAll('.left-panel-'+pageName).style('display', undefined);
    if (pageName == 'country') {
      selectCountry(getState().application.selectedCountryCode);
    } else if (pageName == 'info') {
      if (co2Colorbars) co2Colorbars.forEach(d => { d.render() });
      if (getState().application.windEnabled) if (windColorbar) windColorbar.render();
      if (getState().application.solarEnabled) if (solarColorbar) solarColorbar.render();
    }
  }

  d3.selectAll('#tab .list-item:not(.wind-toggle):not(.solar-toggle)').classed('active', false);
  d3.selectAll('#tab .' + pageName + '-button').classed('active', true);
}

// Initial routing
if (getState().application.showPageState) {
  dispatchApplication('showPageState', getState().application.showPageState);
}

// Now that the width is set, we can render the legends
if (getState().application.windEnabled && !getState().application.selectedCountryCode)
  windColorbar.render();
if (getState().application.solarEnabled && !getState().application.selectedCountryCode)
  solarColorbar.render();

// Attach event handlers
function toggleWind() {
  if (typeof windLayer === 'undefined') { return; }
  dispatchApplication('windEnabled', !getState().application.windEnabled);
}
d3.select('#checkbox-wind').on('change', toggleWind);
d3.select('.wind-toggle').on('click', toggleWind);

function toggleSolar() {
  if (typeof solarLayer === 'undefined') { return; }
  dispatchApplication('solarEnabled', !getState().application.solarEnabled);
}
d3.select('#checkbox-solar').on('change', toggleSolar);
d3.select('.solar-toggle').on('click', toggleSolar);

function mapMouseOver(lonlat) {
  if (getState().application.windEnabled && wind && lonlat && typeof windLayer !== 'undefined') {
    const now = getState().application.customDate ?
      moment(getState().application.customDate) : (new Date()).getTime();
    if (!windLayer.isExpired(now, wind.forecasts[0], wind.forecasts[1])) {
      const u = grib.getInterpolatedValueAtLonLat(lonlat,
        now, wind.forecasts[0][0], wind.forecasts[1][0]);
      const v = grib.getInterpolatedValueAtLonLat(lonlat,
        now, wind.forecasts[0][1], wind.forecasts[1][1]);
      if (!getState().application.selectedCountryCode) {
        windColorbar.currentMarker(Math.sqrt(u * u + v * v));
      }
    }
  } else {
    windColorbar.currentMarker(undefined);
  }
  if (getState().application.solarEnabled && solar && lonlat && typeof solarLayer !== 'undefined') {
    const now = getState().application.customDate ?
      moment(getState().application.customDate) : (new Date()).getTime();
    if (!solarLayer.isExpired(now, solar.forecasts[0], solar.forecasts[1])) {
      const val = grib.getInterpolatedValueAtLonLat(lonlat,
        now, solar.forecasts[0], solar.forecasts[1]);
      if (!getState().application.selectedCountryCode) {
        solarColorbar.currentMarker(val);
      }
    }
  } else {
    solarColorbar.currentMarker(undefined);
  }
}

function renderMap() {
  if (typeof countryMap === 'undefined') { return; }

  if (!mapDraggedSinceStart) {
    const geolocation = callerLocation;
    const { selectedCountryCode } = getState().application;
    if (selectedCountryCode) {
      const lon = d3.mean(countries[selectedCountryCode].coordinates[0][0], d => d[0]);
      const lat = d3.mean(countries[selectedCountryCode].coordinates[0][0], d => d[1]);
      countryMap.setCenter([lon, lat]);
    } else if (geolocation) {
      console.log('Centering on', geolocation);
      countryMap.setCenter(geolocation);
    } else {
      countryMap.setCenter([0, 50]);
    }
  }
  if (exchangeLayer) {
    exchangeLayer.render();
  }

  if (getState().application.windEnabled && wind && wind['forecasts'][0] && wind['forecasts'][1] && typeof windLayer !== 'undefined') {
    LoadingService.startLoading('#loading');
    // Make sure to disable wind if the drawing goes wrong
    Cookies.set('windEnabled', false);
    windLayer.draw(
      getState().application.customDate ?
        moment(getState().application.customDate) : moment(new Date()),
      wind.forecasts[0],
      wind.forecasts[1],
      windColor,
    );
    if (getState().application.windEnabled) {
      windLayer.show();
    } else {
      windLayer.hide();
    }
    // Restore setting
    Cookies.set('windEnabled', getState().application.windEnabled);
    LoadingService.stopLoading('#loading');
  } else {
    windLayer.hide();
  }

  if (getState().application.solarEnabled && solar && solar['forecasts'][0] && solar['forecasts'][1] && typeof solarLayer !== 'undefined') {
    LoadingService.startLoading('#loading');
    // Make sure to disable solar if the drawing goes wrong
    Cookies.set('solarEnabled', false);
    solarLayer.draw(
      getState().application.customDate ? moment(getState().application.customDate) : moment(new Date()),
      solar.forecasts[0],
      solar.forecasts[1],
      solarColor,
      () => {
        if (getState().application.solarEnabled) {
          solarLayer.show();
        } else {
          solarLayer.hide();
        }
        // Restore setting
        Cookies.set('solarEnabled', getState().application.solarEnabled);
        LoadingService.stopLoading('#loading');
      });
  } else {
    solarLayer.hide();
  }
}

let countryListSelector;
// inform the user the last time the map was updated.
function setLastUpdated() {
  currentMoment = (getState().application.customDate && moment(getState().application.customDate) || moment(getState().data.grid.datetime));
  d3.selectAll('.current-datetime').text(currentMoment.format('LL LT'));
  d3.selectAll('.current-datetime-from-now')
    .text(currentMoment.fromNow())
    .style('color', 'darkred')
    .transition()
    .duration(800)
    .style('color', undefined);
}
setInterval(setLastUpdated, 60000);

function dataLoaded(err, clientVersion, argCallerLocation, state, argSolar, argWind) {
  if (err) {
    console.error(err);
    return;
  }

  // Track pageview
  const params = getState().application;
  params.bundleVersion = params.bundleHash;
  params.embeddedUri = params.isEmbedded ? document.referrer : null;
  thirdPartyServices.track('pageview', params);

  // // Debug: randomly generate (consistent) data
  // Object.keys(countries).forEach(function(k) {
  //     if (state.countries[k])
  //         state.countries[k].co2intensity = Math.random() * 800;
  // });
  // Object.keys(exchanges).forEach(function(k) {
  //     if (state.exchanges[k]) {
  //         state.exchanges[k].netFlow = Math.random() * 1500 - 700;
  //         let countries = state.exchanges[k].countryCodes;
  //         let o = countries[(state.exchanges[k].netFlow >= 0) ? 0 : 1]
  //         state.exchanges[k].co2intensity = state.countries[o].co2intensity;
  //     }
  // });
  // // Debug: expose a fetch method
  // window.forceFetchNow = fetch;

  // Is there a new version?
  d3.select('#new-version')
    .classed('active', (clientVersion !== getState().application.bundleHash && !getState().application.isLocalhost && !getState().application.isCordova));

  dispatch({
    payload: state,
    type: 'GRID_DATA',
  });

  // Reset all data we want to update (for instance, not maxCapacity)
  d3.entries(countries).forEach((entry) => {
    entry.value.co2intensity = undefined;
    entry.value.exchange = {};
    entry.value.production = {};
    entry.value.productionCo2Intensities = {};
    entry.value.productionCo2IntensitySources = {};
    entry.value.dischargeCo2Intensities = {};
    entry.value.dischargeCo2IntensitySources = {};
    entry.value.storage = {};
    entry.value.source = undefined;
  });
  d3.entries(exchanges).forEach(function(entry) {
    entry.value.netFlow = undefined;
  });
  histories = {};

  // Populate with realtime country data
  d3.entries(state.countries).forEach(function(entry) {
    let countryCode = entry.key;
    let country = countries[countryCode];
    if (!country) {
      console.warn(countryCode + ' has no country definition.');
      return;
    }
    // Copy data
    d3.keys(entry.value).forEach((k) => {
      // Warning: k takes all values, even those that are not meant to be updated (like maxCapacity)
      country[k] = entry.value[k];
    });
    // Set date
    country.datetime = state.datetime;
    // Validate data
    if (!country.production) return;
    modeOrder.forEach((mode) => {
      if (mode == 'other' || mode == 'unknown' || !country.datetime) { return };
      // Check missing values
      // if (country.production[mode] === undefined && country.storage[mode] === undefined)
      //    console.warn(countryCode + ' is missing production or storage of ' + mode);
      // Check validity of production
      if (country.production[mode] !== undefined && country.production[mode] < 0)
        console.error(countryCode + ' has negative production of ' + mode);
      // Check load factors > 1
      if (country.production[mode] !== undefined &&
        (country.capacity || {})[mode] !== undefined &&
        country.production[mode] > country.capacity[mode])
      {
        console.error(countryCode + ' produces more than its capacity of ' + mode);
      }
    });
    if (!country.exchange || !d3.keys(country.exchange).length)
      console.warn(countryCode + ' is missing exchanges');
  });

  // Render country list
  const validCountries = d3.values(countries).filter(d => {
    return d.co2intensity;
  }).sort((x, y) => {
    if (!x.co2intensity && !x.countryCode)
      return d3.ascending(x.shortname || x.countryCode,
        y.shortname || y.countryCode);
    else
      return d3.ascending(x.co2intensity || Infinity,
        y.co2intensity || Infinity);
  });
  const selector = d3.select('.country-picker-container p')
    .selectAll('a')
    .data(validCountries);
  const enterA = selector.enter().append('a');
  enterA
    .append('div')
    .attr('class', 'emission-rect')
  enterA
    .append('span')
    .attr('class', 'name')
  enterA
    .append('img')
    .attr('class', 'flag')
  enterA
    .append('span')
    .attr('class', 'rank')
  countryListSelector = enterA.merge(selector);
  countryListSelector.select('span.name')
    .text(d => ' ' + (translation.translate('zoneShortName.' + d.countryCode) || d.countryCode) + ' ')
  countryListSelector.select('div.emission-rect')
    .style('background-color', (d) => {
      return d.co2intensity ? co2color(d.co2intensity) : 'gray';
    });
  countryListSelector.select('.flag')
    .attr('src', d => flags.flagUri(d.countryCode, 16));
  countryListSelector.on('click', (d) => {
    dispatchApplication('selectedCountryCode', d.countryCode);
    dispatchApplication('showPageState', 'country');
  });

  if (typeof countryMap !== 'undefined') {
    // Assign country map data
    countryMap
      .setData(d3.values(countries))
      .onCountryMouseOver((d) => {
        tooltipHelper.showMapCountry(countryTooltip, d, co2color, co2Colorbars);
      })
      .onCountryMouseMove((d, i, clientX, clientY, lonlat) => {
        // TODO: Check that i changed before calling showMapCountry
        tooltipHelper.showMapCountry(countryTooltip, d, co2color, co2Colorbars);
        mapMouseOver(lonlat);
        countryTooltip.update(clientX, clientY);
      })
      .onCountryMouseOut((d) => {
        if (co2Colorbars)
          co2Colorbars.forEach((c) => { c.currentMarker(undefined); });
        mapMouseOver(undefined);
        countryTooltip.hide();
      });
  }

  // Add search bar handler
  d3.select('.country-search-bar input')
    .on('keyup', (obj, i, nodes) => {
      const query = nodes[i].value.toLowerCase();

      d3.select('.country-picker-container p')
        .selectAll('a').each((obj, i, nodes) => {
          const countryName = (obj.shortname || obj.countryCode).toLowerCase();
          const listItem = d3.select(nodes[i]);

          if (countryName.indexOf(query) !== -1) {
            listItem.style('display', '');
          } else {
            listItem.style('display', 'none');
          }
        });
    });

  // Re-render country table if it already was visible
  if (getState().application.selectedCountryCode) {
    countryTable.data(countries[getState().application.selectedCountryCode]).render();
  }
  selectCountry(getState().application.selectedCountryCode, true);

  // Populate exchange pairs for arrows
  d3.entries(state.exchanges).forEach((obj) => {
    const exchange = exchanges[obj.key];
    if (!exchange || !exchange.lonlat) {
      console.error('Missing exchange configuration for ' + obj.key);
      return;
    }
    // Copy data
    d3.keys(obj.value).forEach((k) => {
      exchange[k] = obj.value[k];
    });
  });

  // Render exchanges
  if (exchangeLayer) {
    exchangeLayer
      .setData(d3.values(exchanges))
      .render();
  }

  // Render weather if provided
  // Do not overwrite with null/undefined
  if (argWind) wind = argWind;
  if (argSolar) solar = argSolar;
  if (argCallerLocation) callerLocation = argCallerLocation;
  // Update pages that need to be updated
  renderMap();

  // Debug
  console.log(countries);
};

// Periodically load data
function handleConnectionReturnCode(err) {
  if (err) {
    if (err.target) {
      // Avoid catching HTTPError 0
      // The error will be empty, and we can't catch any more info
      // for security purposes
      // See http://stackoverflow.com/questions/4844643/is-it-possible-to-trap-cors-errors
      if (err.target.status) {
        catchError(new Error(
          'HTTPError ' +
          err.target.status + ' ' + err.target.statusText + ' at ' +
          err.target.responseURL + ': ' +
          err.target.responseText));
      }
    } else {
      catchError(err);
    }
    d3.select('#connection-warning').classed('active', true);
  } else {
    d3.select('#connection-warning').classed('active', false);
  }
}

function ignoreError(func) {
  return function() {
    const callback = arguments[arguments.length - 1];
    arguments[arguments.length - 1] = function(err, obj) {
      if (err) {
        return callback(null, null);
      } else {
        return callback(null, obj);
      }
    };
    func.apply(this, arguments);
  };
}

function fetch(showLoading, callback) {
  if (showLoading) LoadingService.startLoading('#loading');
  LoadingService.startLoading('#small-loading');
  const Q = d3.queue();
  // We ignore errors in case this is run from a file:// protocol (e.g. cordova)
  if (getState().application.clientType === 'web' && !getState().application.isLocalhost) {
    Q.defer(d3.text, '/clientVersion');
  } else {
    Q.defer(DataService.fetchNothing);
  }
  Q.defer(DataService.fetchState, ENDPOINT, getState().application.customDate);

  let now = getState().application.customDate || new Date();

  if (!getState().application.solarEnabled)
    Q.defer(DataService.fetchNothing);
  else if (!solar || solarLayer.isExpired(now, solar.forecasts[0], solar.forecasts[1]))
    Q.defer(ignoreError(DataService.fetchGfs), ENDPOINT, 'solar', now);
  else
    Q.defer(function(cb) { return cb(null, solar); });

  if (!getState().application.windEnabled || typeof windLayer === 'undefined')
    Q.defer(DataService.fetchNothing);
  else if (!wind || windLayer.isExpired(now, wind.forecasts[0], wind.forecasts[1]))
    Q.defer(ignoreError(DataService.fetchGfs), ENDPOINT, 'wind', now);
  else
    Q.defer(function(cb) { return cb(null, wind); });
  Q.await(function(err, clientVersion, state, solar, wind) {
    handleConnectionReturnCode(err);
    if (!err)
      dataLoaded(err, clientVersion, state.data.callerLocation, state.data, solar, wind);
    if (showLoading) LoadingService.stopLoading('#loading');
    LoadingService.stopLoading('#small-loading');
    if (callback) callback();
  });
};

function fetchAndReschedule() {
  // TODO(olc): Use `setInterval` instead of `setTimeout`
  if (!getState().application.customDate) {
    return fetch(false, () => {
      setTimeout(fetchAndReschedule, REFRESH_TIME_MINUTES * 60 * 1000);
    });
  }
}

function redraw() {
  if (getState().application.selectedCountryCode) {
    countryTable.render();
    countryHistoryCarbonGraph.render();
    countryHistoryPricesGraph.render();
    countryHistoryMixGraph.render();
  }
  co2Colorbars.forEach(d => { d.render(); });
}

window.addEventListener('resize', () => {
  redraw();
});
window.retryFetch = () => {
  d3.select('#connection-warning').classed('active', false);
  fetch(false);
};

// Observe for navigation
observe(state => state.application.showPageState, (showPageState) => {
  if (showPage) { showPage(showPageState); }
});
// Observe for zoneTable re-render
observe(state => state.countryData, (d) => {
  countryTable.data(d).render(true);
});
// Observe for country change
observe(state => state.application.selectedCountryCode, (k) => {
  selectCountry(k);
});
// Observe for history graph index change
observe(state => state.countryDataIndex, (i) => {
  [countryHistoryCarbonGraph, countryHistoryMixGraph, countryHistoryPricesGraph].forEach((g) => {
    g.selectedIndex(i);
  });
});
// Observe for color blind mode changes
observe(state => state.application.colorBlindModeEnabled, (colorBlindModeEnabled) => {
  Cookies.set('colorBlindModeEnabled', colorBlindModeEnabled);
  updateCo2Scale();
});
// Observe for solar settings change
observe(state => state.application.solarEnabled, (solarEnabled, state) => {
  d3.select('#checkbox-solar').node().checked = solarEnabled;
  d3.selectAll('.solar-toggle').classed('active', solarEnabled);
  d3.select('.solar-colorbar').style('display', solarEnabled ? 'block' : 'none');
  Cookies.set('solarEnabled', solarEnabled);

  const now = state.customDate ?
    moment(state.customDate) : (new Date()).getTime();
  if (solarEnabled) {
    solarColorbar.render();
    if (!solar || solarLayer.isExpired(now, solar.forecasts[0], solar.forecasts[1])) {
      fetch(true);
    } else {
      solarLayer.show();
    }
  } else {
    solarLayer.hide();
  }
});
// Observe for wind settings change
observe(state => state.application.windEnabled, (windEnabled, state) => {
  d3.select('#checkbox-wind').node().checked = windEnabled;
  d3.selectAll('.wind-toggle').classed('active', windEnabled);
  d3.select('.wind-colorbar').style('display', windEnabled ? 'block' : 'none');
  Cookies.set('windEnabled', windEnabled);

  const now = state.customDate ?
    moment(state.customDate) : (new Date()).getTime();
  if (windEnabled) {
    windColorbar.render();
    if (!wind || windLayer.isExpired(now, wind.forecasts[0], wind.forecasts[1])) {
      fetch(true);
    } else {
      windLayer.show();
    }
  } else {
    windLayer.hide();
  }
});
// Observe for changes requiring an update of history
observe(state => state.application, (application) => {
  HistoryState.updateHistoryFromState(application);
});

// Observe for datetimechanes
observe(state => state.data.grid, (grid) => {
  if (grid && grid.datetime) {
    setLastUpdated();
  }
});

// Start a fetch showing loading.
// Later `fetchAndReschedule` won't show loading screen
fetch(true, () => {
  setTimeout(fetchAndReschedule, REFRESH_TIME_MINUTES * 60 * 1000);
});
