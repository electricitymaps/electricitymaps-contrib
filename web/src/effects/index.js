import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';

import thirdPartyServices from '../services/thirdparty';

export function useWidthObserver(ref, offset = 0) {
  const [width, setWidth] = useState(0);

  // Resize hook
  useEffect(() => {
    const updateWidth = () => {
      if (ref.current) {
        setWidth(ref.current.getBoundingClientRect().width - offset);
      }
    };
    // Initialize width if it's not set yet
    if (!width) {
      updateWidth();
    }
    // Update container width on every resize
    window.addEventListener('resize', updateWidth);
    return () => {
      window.removeEventListener('resize', updateWidth);
    };
  });

  return width;
}

export function useHeightObserver(ref, offset = 0) {
  const [height, setHeight] = useState(0);

  // Resize hook
  useEffect(() => {
    const updateHeight = () => {
      if (ref.current) {
        setHeight(ref.current.getBoundingClientRect().height - offset);
      }
    };
    // Initialize height if it's not set yet
    if (!height) {
      updateHeight();
    }
    // Update height on every resize
    window.addEventListener('resize', updateHeight);
    return () => {
      window.removeEventListener('resize', updateHeight);
    };
  });

  return height;
}

export const usePageViewsTracker = () => {
  const { pathname, search } = useLocation();

  // Update GA config whenever the URL changes.
  useEffect(() => {
    if (thirdPartyServices._ga) {
      thirdPartyServices._ga.config({ page_path: `${pathname}${search}` });
    }
  }, [pathname, search]);
};
