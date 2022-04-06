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