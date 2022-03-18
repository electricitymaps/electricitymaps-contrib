import { useEffect, useMemo } from 'react';
import { useLocation } from 'react-router-dom';
import { useDispatch } from 'react-redux';

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
  const { pathname } = useLocation();
  const trackEvent = useTrackEvent();

  // Track app visit once initially.
  useEffect(() => {
    trackEvent('Visit');
  }, []);

  // Track page view whenever the pathname changes (ignore search params changes).
  useEffect(() => {
    trackEvent('pageview');
  }, [pathname]);
};
