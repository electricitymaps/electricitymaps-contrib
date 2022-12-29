import type { ReactElement } from 'react';
import Co2Legend from './Co2Legend';
import {
  selectedDatetimeIndexAtom,
  solarLayerEnabledAtom,
  windLayerAtom,
} from 'utils/state/atoms';
import { useAtom } from 'jotai';
import SolarLegend from './SolarLegend';
import { ToggleOptions } from 'utils/constants';
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
    <div className="invisible fixed bottom-4 right-4 z-50 flex w-[224px]  flex-col rounded bg-white px-1 py-2 shadow dark:bg-gray-900 sm:visible ">
      {isSolarLayerEnabled && <SolarLegend />}
      {isWindLayerEnabled && <WindLegend />}
      <Co2Legend />
    </div>
  );
}
