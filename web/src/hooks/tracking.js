import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

import thirdPartyServices from '../services/thirdparty';

export const usePageViewsTracker = () => {
  const { pathname, search } = useLocation();

  // Track app visit once initially.
  useEffect(() => {
    thirdPartyServices.trackWithCurrentApplicationState('Visit');
  }, []);

  // Update GA config whenever the URL changes.
  useEffect(() => {
    if (thirdPartyServices._ga) {
      thirdPartyServices._ga.config({ page_path: `${pathname}${search}` });
    }
  }, [pathname, search]);

  // Track page view whenever the pathname changes (ignore search params changes).
  useEffect(() => {
    thirdPartyServices.trackWithCurrentApplicationState('pageview');
  }, [pathname]);
};
