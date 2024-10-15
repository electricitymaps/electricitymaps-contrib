import { RefObject, useEffect } from 'react';
import { useLocation } from 'react-router-dom';

import { useClearFragment } from './useClearFragment';

export function useScrollAnchorIntoView(reference: RefObject<HTMLElement | undefined>) {
  const { hash } = useLocation();
  const clearFragment = useClearFragment();
  useEffect(() => {
    if (reference.current?.id === hash.slice(1)) {
      reference.current.scrollIntoView({ behavior: 'smooth' });
      clearFragment();
    }
  }, [hash, clearFragment, reference]);

  return;
}
