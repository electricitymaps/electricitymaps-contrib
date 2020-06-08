import * as request from 'd3-request';

export function clientVersionRequest() {
  return new Promise((resolve, reject) => {
    request.text('/clientVersion').get(null, (err, res) => {
      if (err) {
        reject(err);
      } else if (!res) {
        reject(new Error('Empty response received for the client version'));
      } else {
        resolve(res);
      }
    });
  });
}
