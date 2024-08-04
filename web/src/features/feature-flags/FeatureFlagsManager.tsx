import * as Switch from '@radix-ui/react-switch';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Meta } from 'api/getMeta';
import { QUERY_KEYS } from 'api/helpers';

import { useFeatureFlags } from './api';
import { FeatureFlags } from './types';

function handleClearLocalStorage() {
  localStorage.clear();
  location.reload();
}

function Content({ features }: { features: FeatureFlags }) {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    // Leaving an empty function here as we only want to apply mutation locally
    mutationFn: (_key: string) => Promise.resolve(),
    onMutate: async (key) => {
      // Snapshot the previous value
      const previousState = queryClient.getQueryData([QUERY_KEYS.META]);

      // Optimistically update to the new value
      queryClient.setQueryData([QUERY_KEYS.META], (previousMeta: Meta | undefined) => {
        const previousFeatures = previousMeta?.features || {};
        return {
          ...previousMeta,
          features: {
            ...previousFeatures,
            [key]: !previousFeatures?.[key],
          },
        };
      });

      // Return a context object with the snapshotted value
      return { previousState };
    },
  });

  return (
    <div className="flex flex-col">
      <p className="pb-1 font-poppins text-sm text-gray-600">Feature Flags</p>
      <div>
        {Object.entries(features).map(([key, value]) => (
          <div className="flex w-full items-center justify-between text-sm" key={key}>
            <label className="pr-8" htmlFor={key}>
              {key}
            </label>
            <Switch.Root
              className="relative h-[20px] w-[38px] cursor-default rounded-full bg-gray-300 outline-none data-[state=checked]:bg-brand-green"
              id={key}
              defaultChecked={Boolean(value)}
              onCheckedChange={() => mutation.mutate(key)}
            >
              <Switch.Thumb className="block h-[16px] w-[16px] translate-x-0.5 rounded-full bg-white transition-transform duration-100 will-change-transform data-[state=checked]:translate-x-[19px]" />
            </Switch.Root>
          </div>
        ))}
      </div>
      <button
        className="mt-2 self-end rounded  bg-green-900 p-1 text-sm text-white"
        onClick={handleClearLocalStorage}
      >
        Clear Local Storage
      </button>
    </div>
  );
}

export default function FeatureFlagsManager() {
  const features = useFeatureFlags();

  if (!features) {
    return null;
  }

  return (
    <div className="pointer-events-auto invisible flex w-[224px] flex-col rounded bg-white/90 px-4 py-4 shadow-lg backdrop-blur-sm dark:bg-gray-800 sm:visible">
      <Content features={features} />
    </div>
  );
}
