const thirdPartyServices = require('../services/thirdparty');

// History state init (state that is reflected in the url)
const historyState = {};

// Map from querystring key to state key
const querystringMappings = {
  countryCode: 'selectedCountryCode',
  datetime: 'customDate',
  page: 'showPageState',
  solar: 'solarEnabled',
  remote: 'useRemoteEndpoint',
  wind: 'windEnabled',
};
const reverseQuerystringMappings = {};
Object.keys(querystringMappings).forEach((k) => {
  reverseQuerystringMappings[querystringMappings[k]] = k;
});

function appendQueryString(url, key, value) {
  return (url === '?' ? url : url + '&') + key + '=' + value;
}

function getURL() {
  let url = '?';
  Object.keys(historyState).forEach((k) => {
    url = appendQueryString(url, k, historyState[k]);
  });
  // '.' is not supported when serving from file://
  return (url === '?' ? '?' : url);
}

function replace(key, value) {
  if (value == null) {
    delete historyState[key];
  } else {
    historyState[key] = value;
  }
}

function updateHistoryFromState(applicationState) {
  // `state` is the redux application state
  Object.keys(querystringMappings).forEach((historyKey) => {
    replace(historyKey, applicationState[querystringMappings[historyKey]]);
  });
  const url = getURL();
  if (thirdPartyServices._ga) {
    thirdPartyServices._ga.config({ page_path: url });
  }
  window.history.replaceState(historyState, '', url);
}

function getStateFromHistory() {
  const result = {};
  Object.keys(historyState).forEach((k) => {
    result[querystringMappings[k]] = historyState[k];
  });
  return result;
}

// Parse initial history state
const querystrings = window.location.search.replace('\?','').split('&');
const validKeys = Object.keys(querystringMappings);
querystrings.forEach((d) => {
  const pair = d.split('=');
  const [k, v] = pair;
  if (validKeys.indexOf(k) !== -1) {
    if (['true', 'false'].indexOf(v.toLowerCase()) !== -1) {
      replace(k, v.toLowerCase() === 'true');
    } else {
      replace(k, v);
    }
  }
});

// We can watch the values of querystringMappings to know which redux keys to...

// args.forEach((arg) => {
//   } else if (kv[0] == 'datetime') {
//     customDate = kv[1];
//     // HACK
//     window.customDate = customDate;
//     replaceHistoryState('datetime', customDate);
//   } else if (kv[0] == 'page') {
//     showPageState = kv[1].replace('%20', '');
//     replaceHistoryState('page', showPageState);
//     if (showPage) showPage(showPageState);
// });

module.exports = { getStateFromHistory, updateHistoryFromState };
