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
    <div className="invisible  flex w-[224px] flex-col rounded bg-white/90 px-1 py-2 shadow-xl backdrop-blur-sm sm:visible dark:bg-gray-800">
      {isSolarLayerEnabled && <SolarLegend />}
      {isWindLayerEnabled && <WindLegend />}
      <Co2Legend />
    </div>
  );
}
