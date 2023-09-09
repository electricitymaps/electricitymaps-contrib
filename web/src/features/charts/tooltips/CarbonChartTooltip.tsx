/* eslint-disable unicorn/no-null */
import { CarbonIntensityDisplay } from 'components/CarbonIntensityDisplay';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtom } from 'jotai';
import { useTranslation } from 'translation/translation';
import { Mode } from 'utils/constants';
import { getCarbonIntensity } from 'utils/helpers';
import { productionConsumptionAtom, timeAverageAtom } from 'utils/state/atoms';
import { InnerAreaGraphTooltipProps } from '../types';
import AreaGraphToolTipHeader from './AreaGraphTooltipHeader';

export default function CarbonChartTooltip({ zoneDetail }: InnerAreaGraphTooltipProps) {
  const [timeAverage] = useAtom(timeAverageAtom);
  const { __ } = useTranslation();
  const [currentMode] = useAtom(productionConsumptionAtom);
  const isConsumption = currentMode === Mode.CONSUMPTION;
  const co2ColorScale = useCo2ColorScale();

  if (!zoneDetail) {
    return null;
  }
  const { co2intensity, co2intensityProduction, stateDatetime } = zoneDetail;
  const intensity = getCarbonIntensity(
    isConsumption,
    co2intensity,
    co2intensityProduction
  );
  return (
    <div
      data-test-id="carbon-chart-tooltip"
      className="w-full rounded-md bg-white p-3 shadow-xl dark:border dark:border-gray-700 dark:bg-gray-800 sm:w-80"
    >
      <AreaGraphToolTipHeader
        datetime={new Date(stateDatetime)}
        timeAverage={timeAverage}
        squareColor={co2ColorScale(intensity)}
        title={__('tooltips.carbonintensity')}
      />
      <CarbonIntensityDisplay
        co2Intensity={intensity}
        className="flex justify-center text-base"
      />
    </div>
  );
}
