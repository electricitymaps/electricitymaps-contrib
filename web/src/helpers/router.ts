// @ts-expect-error TS(7016): Could not find a declaration file for module 'hist... Remove this comment to see the full error message
import { createBrowserHistory, createHashHistory } from 'history';

// Use BrowserHistory in the web browser and HashHistory
// in the mobile apps as we need to keep relative resource
// paths for the mobile which are fundamentally incompatible
// with browser side URL paths routing.
// TODO: Replace this with React Router DOM
// `useHistory` hook after full migration to React.
export const history = (window as any).isCordova ? createHashHistory() : createBrowserHistory();

// TODO: Deprecate in favor of React Router useParams (requires move to React)
export function getZoneId() {
  return history.location.pathname.split('/')[2];
}
