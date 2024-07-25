import { useAtomValue } from 'jotai';
import type { ReactElement } from 'react';
import { isSolarLayerEnabledAtom, isWindLayerEnabledAtom } from 'utils/state/atoms';

import Co2Legend from './Co2Legend';
import SolarLegend from './SolarLegend';
import WindLegend from './WindLegend';

export default function LegendContainer(): ReactElement {
  const isSolarLayerEnabled = useAtomValue(isSolarLayerEnabledAtom);
  const isWindLayerEnabled = useAtomValue(isWindLayerEnabledAtom);

  return (
    <div className="flex w-[224px] flex-col rounded-2xl bg-white/80 px-2 pb-2 pt-4 backdrop-blur dark:bg-gray-800/80">
      {isSolarLayerEnabled && <SolarLegend />}
      {isWindLayerEnabled && <WindLegend />}
      <Co2Legend />
    </div>
  );
}
