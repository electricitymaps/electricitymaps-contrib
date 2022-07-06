import { useMemo } from 'react';
import { useDispatch } from 'react-redux';

export const useTrackEvent = () => {
  const dispatch = useDispatch();

  return useMemo(
    () => (eventName, context) => {
      dispatch({ type: 'TRACK_EVENT', payload: { eventName, context } });
    },
    [dispatch]
  );
};
