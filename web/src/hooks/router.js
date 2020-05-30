import { useMemo } from 'react';
import { useLocation } from 'react-router-dom';

export function useSearchParams() {
  return new URLSearchParams(useLocation().search);
}

export function useCustomDatetime() {
  return useSearchParams().get('datetime');
}

export function useSolarEnabled() {
  return useSearchParams().get('solar') === 'true';
}

export function useWindEnabled() {
  return useSearchParams().get('wind') === 'true';
}

export function useSolarToggledLocation() {
  const location = useLocation();
  const searchParams = useSearchParams();
  const solarEnabled = useSolarEnabled();

  return useMemo(
    () => {
      searchParams.set('solar', !solarEnabled);
      return {
        pathname: location.pathname,
        search: searchParams.toString(),
      };
    },
    [location, searchParams, solarEnabled],
  );
}

export function useWindToggledLocation() {
  const location = useLocation();
  const searchParams = useSearchParams();
  const windEnabled = useWindEnabled();

  return useMemo(
    () => {
      searchParams.set('wind', !windEnabled);
      return {
        pathname: location.pathname,
        search: searchParams.toString(),
      };
    },
    [location, searchParams, windEnabled],
  );
}
