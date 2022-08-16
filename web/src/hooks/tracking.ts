import { useMemo } from 'react';
import { useDispatch } from 'react-redux';

export const useTrackEvent = () => {
  const dispatch = useDispatch();

  return useMemo(
    () => (eventName: any, context: any) => {
      dispatch({ type: 'TRACK_EVENT', payload: { eventName, context } });
    },
    [dispatch]
  );
};
