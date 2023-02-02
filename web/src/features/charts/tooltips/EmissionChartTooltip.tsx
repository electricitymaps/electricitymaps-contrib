import { useAtom } from 'jotai';
import { useTranslation } from 'translation/translation';
import { timeAverageAtom } from 'utils/state/atoms';
import { getTotalElectricity, tonsPerHourToGramsPerMinute } from '../graphUtils';
import { InnerAreaGraphTooltipProps } from '../types';
import AreaGraphToolTipHeader from './AreaGraphTooltipHeader';

export default function EmissionChartTooltip({ zoneDetail }: InnerAreaGraphTooltipProps) {
  const [timeAverage] = useAtom(timeAverageAtom);
  const { __ } = useTranslation();

  if (!zoneDetail) {
    return null;
  }

  const totalEmissions =
    Math.round(tonsPerHourToGramsPerMinute(getTotalElectricity(zoneDetail, true)) * 100) /
    100;
  const { stateDatetime } = zoneDetail;

  return (
    <div className="w-full rounded-md bg-white p-3 shadow-xl dark:bg-gray-900 sm:w-[350px]">
      <AreaGraphToolTipHeader
        datetime={new Date(stateDatetime)}
        timeAverage={timeAverage}
        squareColor="#a5292a"
        title={__('country-panel.emissions')}
      />
      <p className="flex justify-center text-base">
        <b className="mr-1">{totalEmissions}t</b> {__('ofCO2eqPerMinute')}
      </p>
    </div>
  );
}
