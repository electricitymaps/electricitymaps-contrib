import { extent } from 'd3-array';
import { scaleLinear } from 'd3-scale';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtom } from 'jotai/index';
import { memo, type ReactElement, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { CarbonUnits } from 'utils/units';

import { useFeatureFlag } from '../../features/feature-flags/api';
import { co2IntensityRangeAtom } from '../../utils/state/atoms';
import RangeSlider from '../RangeSlider';
import HorizontalColorbar, { spreadOverDomain } from './ColorBar';
import { LegendItem } from './LegendItem';

const TICKS_COUNT = 6;

function Co2Legend(): ReactElement {
  const isCo2IntensityFilteringFeatureEnabled = useFeatureFlag(
    'legend-co2-intensity-filtering'
  );
  const { t } = useTranslation();
  const co2ColorScale = useCo2ColorScale();

  const rangeValues = useMemo(
    () =>
      spreadOverDomain(
        scaleLinear().domain(
          extent(co2ColorScale.domain()) as unknown as [number, number]
        ),
        TICKS_COUNT
      ),
    [co2ColorScale]
  );

  const [co2IntensityRange, setCo2IntensityRange] = useAtom(co2IntensityRangeAtom);
  const defaultValue = useMemo(
    () => [rangeValues.at(0) as number, rangeValues.at(-1) as number],
    [rangeValues]
  );

  return (
    <LegendItem
      label={t('legends.carbonintensity')}
      unit={CarbonUnits.GRAMS_CO2EQ_PER_KILOWATT_HOUR}
    >
      {isCo2IntensityFilteringFeatureEnabled ? (
        <RangeSlider
          value={co2IntensityRange}
          defaultValue={defaultValue}
          onChange={setCo2IntensityRange}
          maxValue={rangeValues.at(-1) as number}
          step={20}
          trackComponent={
            <HorizontalColorbar
              colorScale={co2ColorScale}
              ticksCount={TICKS_COUNT}
              id={'co2'}
              labelClassNames="mt-1"
            />
          }
        />
      ) : (
        <HorizontalColorbar
          colorScale={co2ColorScale}
          ticksCount={TICKS_COUNT}
          id={'co2'}
        />
      )}
    </LegendItem>
  );
}

export default memo(Co2Legend);
