import { useAtom } from 'jotai';
import { useTranslation } from 'translation/translation';
import { displayByEmissionsAtom, timeAverageAtom } from 'utils/state/atoms';
import { InnerAreaGraphTooltipProps } from '../types';
import AreaGraphToolTipHeader from './AreaGraphTooltipHeader';
import { getNetExchange, round } from 'utils/helpers';
import { scalePower } from 'utils/formatting';

export default function NetExchangeChartTooltip({
  zoneDetail,
}: InnerAreaGraphTooltipProps) {
  if (!zoneDetail) {
    return null;
  }
  const [timeAverage] = useAtom(timeAverageAtom);
  const [displayByEmissions] = useAtom(displayByEmissionsAtom);
  const { __ } = useTranslation();

  const { stateDatetime } = zoneDetail;

  const netExchange = getNetExchange(zoneDetail, displayByEmissions);
  const { formattingFactor, unit } = displayByEmissions
    ? {
        formattingFactor: 1,
        unit: 'tCO₂eq / min',
      }
    : scalePower(netExchange);

  return (
    <div className="w-full rounded-md bg-white p-3 shadow-xl dark:bg-gray-900 sm:w-max">
      <AreaGraphToolTipHeader
        datetime={new Date(stateDatetime)}
        timeAverage={timeAverage}
        squareColor="#7f7f7f"
        title={__('tooltips.netExchange')}
      />
      <p className="flex justify-center text-base">
        {netExchange >= 0 ? __('tooltips.importing') : __('tooltips.exporting')}{' '}
        <b className="mx-1">{Math.abs(round(netExchange / formattingFactor))}</b> {unit}
      </p>
    </div>
  );
}
