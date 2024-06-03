import { useMeta } from 'api/getMeta';

import { FeatureFlags } from './types';

export function useFeatureFlags(): FeatureFlags {
  const { features } = useMeta();
  return features || {};
}

export function useFeatureFlag(name: string): boolean {
  const { features } = useMeta();

  return features?.[name] || false;
}
