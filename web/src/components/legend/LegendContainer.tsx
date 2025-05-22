import GlassContainer from 'components/GlassContainer';
import { useAtomValue } from 'jotai';
import { memo, type ReactElement } from 'react';
import { isSolarLayerEnabledAtom, isWindLayerEnabledAtom } from 'utils/state/atoms';

import Legend from './MapColorLegend';
import SolarLegend from './SolarLegend';
import WindLegend from './WindLegend';

function LegendContainer(): ReactElement {
  const isSolarLayerEnabled = useAtomValue(isSolarLayerEnabledAtom);
  const isWindLayerEnabled = useAtomValue(isWindLayerEnabledAtom);

  return (
    <GlassContainer className="pointer-events-auto relative  min-w-64 max-w-min flex-col gap-2  p-2">
      {isSolarLayerEnabled && <SolarLegend />}
      {isWindLayerEnabled && <WindLegend />}
      <Legend />
    </GlassContainer>
  );
}

export default memo(LegendContainer);
