import * as request from 'd3-request';
import { sha256 } from 'js-sha256';
import Cookies from 'js-cookie';

import { isLocalhost } from './environment';
import thirdPartyServices from '../services/thirdparty';

function getToken() {
  if (ELECTRICITYMAP_PUBLIC_TOKEN === '%SNOWPACK_PUBLIC_ELECTRICITYMAP_PUBLIC_TOKEN%') {
    throw new Error(
      'It seems like you are trying to run the app locally with remote API, but have not set the SNOWPACK_PUBLIC_ELECTRICITYMAP_PUBLIC_TOKEN environment variable.\n Try running `SNOWPACK_PUBLIC_ELECTRICITYMAP_PUBLIC_TOKEN=<your-token> yarn develop`'
    );
  }
  return ELECTRICITYMAP_PUBLIC_TOKEN;
}

function isRemoteParam() {
  return new URLSearchParams(window.location.search).get('remote') === 'true';
}

// Use local endpoint only if ALL of the following conditions are true:
// 1. The app is running on localhost
// 2. The `remote` search param hasn't been explicitly set to true
// 3. Document domain has a non-empty value
function isUsingLocalEndpoint() {
  return isLocalhost() && !isRemoteParam() && document.domain !== '';
}

export function getEndpoint() {
  return isUsingLocalEndpoint() ? 'http://localhost:8001' : 'https://app-backend.electricitymap.org';
}

export function protectedJsonRequest(path) {
  const url = getEndpoint() + path;
  const token = isUsingLocalEndpoint() ? 'development' : getToken();
  const timestamp = new Date().getTime();

  return new Promise((resolve, reject) => {
    request
      .json(url)
      .header('electricitymap-token', Cookies.get('electricitymap-token'))
      .header('x-request-timestamp', timestamp)
      .header('x-signature', sha256(token + path + timestamp))
      .get(null, (err, res) => {
        if (err) {
          reject(err);
        } else if (!res || !res.data) {
          const errorToReturn = new Error(`Empty response received for ${url}`);
          // Treat as a 404
          errorToReturn.target = {
            status: 404,
            statusText: errorToReturn.message,
          };
          reject(errorToReturn);
        } else {
          resolve(res.data);
        }
      });
  });
}

export function handleRequestError(err) {
  if (err) {
    if (err.target) {
      const { responseText, responseURL, status, statusText } = err.target;

      // Avoid catching HTTPError 0
      // The error will be empty, and we can't catch any more info for security purposes.
      // See http://stackoverflow.com/questions/4844643/is-it-possible-to-trap-cors-errors
      if (!status) {
        return;
      }

      // Also ignore 5xx errors as they are usually caused by server downtime and are not useful to track.
      if ((status >= 500 && status <= 599) || status === 404) {
        return;
      }

      thirdPartyServices.trackError(new Error(`HTTPError ${status} ${statusText} at ${responseURL}: ${responseText}`));
    } else {
      thirdPartyServices.trackError(err);
    }
  }
}
