import { useAtomValue } from 'jotai';
import { memo, type ReactElement } from 'react';
import { isSolarLayerEnabledAtom, isWindLayerEnabledAtom } from 'utils/state/atoms';

import Co2Legend from './Co2Legend';
import SolarLegend from './SolarLegend';
import WindLegend from './WindLegend';

function LegendContainer(): ReactElement {
  const isSolarLayerEnabled = useAtomValue(isSolarLayerEnabledAtom);
  const isWindLayerEnabled = useAtomValue(isWindLayerEnabledAtom);

  return (
    <div className="flex min-w-64 max-w-min flex-col gap-2 rounded-2xl border border-neutral-200/80 bg-white/80 p-2 backdrop-blur dark:border-gray-700/80 dark:bg-gray-800/80">
      {isSolarLayerEnabled && <SolarLegend />}
      {isWindLayerEnabled && <WindLegend />}
      <Co2Legend />
    </div>
  );
}

export default memo(LegendContainer);
