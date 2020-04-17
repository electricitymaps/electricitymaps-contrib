import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

import thirdPartyServices from '../services/thirdparty';

export const usePageViewsTracker = () => {
  const { pathname, search } = useLocation();

  // Update GA config whenever the URL changes.
  useEffect(() => {
    if (thirdPartyServices._ga) {
      thirdPartyServices._ga.config({ page_path: `${pathname}${search}` });
    }
  }, [pathname, search]);
};
