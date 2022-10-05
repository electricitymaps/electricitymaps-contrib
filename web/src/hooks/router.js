import { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { useLocation } from 'react-router-dom';
import { TIME } from '../helpers/constants';

export function useSearchParams() {
  const { search } = useLocation();
  return useMemo(() => {
    return new URLSearchParams(search);
  }, [search]);
}

export function useFeatureToggle(selectedFeature = null) {
  const searchParams = useSearchParams();
  const featureToggles = searchParams.get('feature');

  return useMemo(() => {
    if (selectedFeature) {
      return featureToggles && featureToggles.split(',').includes(selectedFeature);
    } else {
      return featureToggles ? featureToggles.split(',') : [];
    }
  }, [selectedFeature, featureToggles]);
}

export function useHeaderVisible() {
  return useSearchParams().get('header') !== 'false';
}

export function useSolarEnabled() {
  const isWeatherEnabled = useSelector(
    (state) => state.application.selectedTimeAggregate === TIME.HOURLY && state.application.selectedZoneTimeIndex === 24
  );
  return useSearchParams().get('solar') === 'true' && isWeatherEnabled;
}

export function useWindEnabled() {
  const isWeatherEnabled = useSelector(
    (state) => state.application.selectedTimeAggregate === TIME.HOURLY && state.application.selectedZoneTimeIndex === 24
  );
  return useSearchParams().get('wind') === 'true' && isWeatherEnabled;
}

export const useAggregatesEnabled = () => {
  return useSearchParams().get('aggregated') === 'true';
};

export const useAggregatesToggle = () => {
  const location = useLocation();
  const searchParams = useSearchParams();
  const aggregatesEnabled = useAggregatesEnabled();

  searchParams.set('aggregated', !aggregatesEnabled);
  return {
    pathname: location.pathname,
    search: searchParams.toString(),
  };
};

export function useSolarToggledLocation() {
  const location = useLocation();
  const searchParams = useSearchParams();
  const solarEnabled = useSolarEnabled();

  return useMemo(() => {
    searchParams.set('solar', !solarEnabled);
    return {
      pathname: location.pathname,
      search: searchParams.toString(),
    };
  }, [location, searchParams, solarEnabled]);
}

export function useWindToggledLocation() {
  const location = useLocation();
  const searchParams = useSearchParams();
  const windEnabled = useWindEnabled();

  return useMemo(() => {
    searchParams.set('wind', !windEnabled);
    return {
      pathname: location.pathname,
      search: searchParams.toString(),
    };
  }, [location, searchParams, windEnabled]);
}
