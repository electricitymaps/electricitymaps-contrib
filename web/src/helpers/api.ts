// @ts-expect-error TS(7016): Could not find a declaration file for module 'd3-r... Remove this comment to see the full error message
import * as request from 'd3-request';
// @ts-expect-error TS(7016): Could not find a declaration file for module 'js-c... Remove this comment to see the full error message
import Cookies from 'js-cookie';

import { isLocalhost } from './environment';
import thirdPartyServices from '../services/thirdparty';
import { isRemoteParam } from './featureFlags';

function getToken() {
  // @ts-expect-error TS(2304): Cannot find name 'ELECTRICITYMAP_PUBLIC_TOKEN'.
  if (ELECTRICITYMAP_PUBLIC_TOKEN === '%SNOWPACK_PUBLIC_ELECTRICITYMAP_PUBLIC_TOKEN%') {
    throw new Error(
      'It seems like you are trying to run the app locally with remote API, but have not set the SNOWPACK_PUBLIC_ELECTRICITYMAP_PUBLIC_TOKEN environment variable.\n Try running `SNOWPACK_PUBLIC_ELECTRICITYMAP_PUBLIC_TOKEN=<your-token> yarn develop`'
    );
  }
  // @ts-expect-error TS(2304): Cannot find name 'ELECTRICITYMAP_PUBLIC_TOKEN'.
  return ELECTRICITYMAP_PUBLIC_TOKEN;
}

// Use local endpoint only if ALL of the following conditions are true:
// 1. The app is running on localhost
// 2. The `remote` search param hasn't been explicitly set to true
// 3. Document domain has a non-empty value
function isUsingLocalEndpoint() {
  return isLocalhost() && !isRemoteParam() && document.domain !== '';
}

async function sha256(message) {
  const hashBuffer = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(message));
  return Array.from(new Uint8Array(hashBuffer))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

export function getEndpoint() {
  return isUsingLocalEndpoint() ? 'http://localhost:8001' : 'https://app-backend.electricitymap.org';
}

export async function protectedJsonRequest(path: any) {
  const url = getEndpoint() + path;
  const token = isUsingLocalEndpoint() ? 'development' : getToken();
  const timestamp = new Date().getTime();
  const signature = await sha256(token + path + timestamp);

  return new Promise((resolve, reject) => {
    request
      .json(url)
      .header('electricitymap-token', Cookies.get('electricitymap-token'))
      .header('x-request-timestamp', timestamp)
      .header('x-signature', signature)
      .get(null, (err: any, res: any) => {
        if (err) {
          reject(err);
        } else if (!res || !res.data) {
          const errorToReturn = new Error(`Empty response received for ${url}`);
          // Treat as a 404
          (errorToReturn as any).target = {
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

export function handleRequestError(err: any) {
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
