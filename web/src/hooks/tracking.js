import { useEffect, useMemo } from 'react';
import { useLocation } from 'react-router-dom';
import { useDispatch } from 'react-redux';

import thirdPartyServices from '../services/thirdparty';

export const useTrackEvent = () => {
  const dispatch = useDispatch();

  return useMemo(
    () => (eventName, context) => {
      dispatch({ type: 'TRACK_EVENT', payload: { eventName, context } });
    },
    [dispatch],
  );
};

export const usePageViewsTracker = () => {
  const { pathname, search } = useLocation();
  const trackEvent = useTrackEvent();

  // Track app visit once initially.
  useEffect(() => {
    trackEvent('Visit');
  }, [trackEvent]);

  // Update GA config whenever the URL changes.
  useEffect(() => {
    if (thirdPartyServices._ga) {
      thirdPartyServices._ga.config({ page_path: `${pathname}${search}` });
    }
  }, [pathname, search, trackEvent]);

  // Track page view whenever the pathname changes (ignore search params changes).
  useEffect(() => {
    trackEvent('pageview');
  }, [pathname, trackEvent]);
};
