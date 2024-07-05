import { useAtom } from 'jotai';
import type { ReactElement } from 'react';
import { ToggleOptions } from 'utils/constants';
import {
  selectedDatetimeIndexAtom,
  solarLayerEnabledAtom,
  windLayerAtom,
} from 'utils/state/atoms';

import Co2Legend from './Co2Legend';
import SolarLegend from './SolarLegend';
import WindLegend from './WindLegend';

export default function LegendContainer(): ReactElement {
  const [solarLayerToggle] = useAtom(solarLayerEnabledAtom);
  const [windLayerToggle] = useAtom(windLayerAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);

  const isSolarLayerEnabled =
    solarLayerToggle === ToggleOptions.ON && selectedDatetime.index === 24;
  const isWindLayerEnabled =
    windLayerToggle === ToggleOptions.ON && selectedDatetime.index === 24;

  return (
    <div className="flex w-[224px] flex-col rounded-2xl bg-white/80 px-2 pb-2 pt-4 backdrop-blur dark:bg-gray-800/80">
      {isSolarLayerEnabled && <SolarLegend />}
      {isWindLayerEnabled && <WindLegend />}
      <Co2Legend />
    </div>
  );
}
