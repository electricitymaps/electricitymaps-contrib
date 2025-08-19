import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

import { pushToDataLayer } from '../utils/gtm';

/**
 * Component that tracks page views for Single Page Applications (SPAs)
 * using React Router and sends the data to GTM via the conditional
 * pushToDataLayer helper. This ensures tracking only occurs in the
 * web environment.
 */
function GtmPageTracker(): null {
  const location = useLocation();

  useEffect(() => {
    // Use the document title for pageTitle. Ensure your routing/
    // components set the document title appropriately for accurate tracking.
    const pageTitle = document.title;

    // Push the page_view event to the data layer on initial load and route change
    // The pushToDataLayer function handles the conditional logic (web vs native)
    pushToDataLayer({
      event: 'page_view',
      pagePath: location.pathname + location.search + location.hash,
      pageTitle: pageTitle,
    });
  }, [location]); // Rerun effect when location changes

  return null; // This component does not render anything
}

export default GtmPageTracker;
