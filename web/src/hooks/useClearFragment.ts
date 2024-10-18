import { useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

export function useClearFragment() {
  const navigate = useNavigate();
  const location = useLocation();

  return useCallback(() => {
    navigate(`${location.pathname}${location.search}`);
  }, [navigate, location.pathname, location.search]);
}
