import { useAtom } from 'jotai';
import { useTranslation } from 'translation/translation';
import { productionConsumptionAtom, timeAverageAtom } from 'utils/state/atoms';
import { getTotalElectricity } from '../graphUtils';
import { InnerAreaGraphTooltipProps } from '../types';
import AreaGraphToolTipHeader from './AreaGraphTooltipHeader';
import { formatCo2 } from 'utils/formatting';

export default function EmissionChartTooltip({ zoneDetail }: InnerAreaGraphTooltipProps) {
  const [timeAverage] = useAtom(timeAverageAtom);
  const [mixMode] = useAtom(productionConsumptionAtom);
  const { __ } = useTranslation();

  if (!zoneDetail) {
    return null;
  }

  const totalEmissions = getTotalElectricity(zoneDetail, true, mixMode);
  const { stateDatetime } = zoneDetail;

  return (
    <div className="w-full rounded-md bg-white p-3 shadow-xl dark:border dark:border-gray-700 dark:bg-gray-800 sm:w-[350px]">
      <AreaGraphToolTipHeader
        datetime={new Date(stateDatetime)}
        timeAverage={timeAverage}
        squareColor="#a5292a"
        title={__('country-panel.emissions')}
      />
      <p className="flex justify-center text-base">
        <b className="mr-1">{formatCo2(totalEmissions)}</b> {__('ofCO2eqPerMinute')}
      </p>
    </div>
  );
}
