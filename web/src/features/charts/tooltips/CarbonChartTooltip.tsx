/* eslint-disable unicorn/no-null */
import { CarbonIntensityDisplay } from 'components/CarbonIntensity';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { formatDate } from 'utils/formatting';
import { productionConsumptionAtom, timeAverageAtom } from 'utils/state/atoms';
import { InnerAreaGraphTooltipProps } from '../types';
import { Mode } from 'utils/constants';

export default function CarbonChartTooltip(props: InnerAreaGraphTooltipProps) {
  const [timeAverage] = useAtom(timeAverageAtom);
  const { i18n } = useTranslation();
  const { zoneDetail } = props;
  const [currentMode] = useAtom(productionConsumptionAtom);
  const isConsumption = currentMode === Mode.CONSUMPTION;

  const co2ColorScale = useCo2ColorScale();

  if (!zoneDetail) {
    return null;
  }
  const { co2intensity, co2intensityProduction, stateDatetime } = zoneDetail;
  const intensity = (isConsumption ? co2intensity : co2intensityProduction) ?? 0;
  return (
    <div className="w-full rounded-md bg-white p-3 shadow-xl dark:bg-gray-900 sm:w-80">
      <div className="flex justify-between">
        <div className="inline-flex items-center gap-x-1">
          <div
            style={{
              backgroundColor: co2ColorScale(intensity),
            }}
            className="h-[16px] w-[16px] rounded-sm"
          ></div>
          <div className="text-base font-bold">Carbon Intensity</div>
        </div>
        <div className="my-1 h-[32px] max-w-[160px] select-none rounded-full bg-brand-green/10 py-2 px-3 text-sm text-brand-green dark:bg-gray-700 dark:text-white">
          {formatDate(new Date(stateDatetime), i18n.language, timeAverage)}
        </div>
      </div>
      <hr className="my-1 mb-3" />
      <p className="flex justify-center text-base">
        <CarbonIntensityDisplay co2Intensity={intensity} />
      </p>
    </div>
  );
}
