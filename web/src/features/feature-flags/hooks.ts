import { useQuery } from '@tanstack/react-query';
import { QUERY_KEYS } from 'api/helpers';
import { getFeatureFlags } from './api';
import { FeatureFlags } from './types';

export function useFeatureFlags(): FeatureFlags {
  return (
    useQuery<FeatureFlags>([QUERY_KEYS.FEATURE_FLAGS], async () => getFeatureFlags(), {
      suspense: true,
    }).data || {}
  );
}

export function useFeatureFlag(name: string): boolean {
  const features = useFeatureFlags();

  return features?.[name] || false;
}
