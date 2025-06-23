import { useMeta } from 'api/getMeta';

import { FeatureFlags } from './types';

export function useFeatureFlags(): FeatureFlags {
  const { features } = useMeta();
  return features || {};
}

export function useFeatureFlag(name: string): boolean {
  const { features } = useMeta();
  if (name === 'legend-co2-intensity-filtering') {
    return true;
  } // todo remove before commit
  return features?.[name] || false;
}
