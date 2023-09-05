import { useAtom } from 'jotai';
import { useTranslation } from 'translation/translation';
import { getNetExchange, round } from 'utils/helpers';
import { displayByEmissionsAtom, timeAverageAtom } from 'utils/state/atoms';
import { InnerAreaGraphTooltipProps } from '../types';
import AreaGraphToolTipHeader from './AreaGraphTooltipHeader';
import { formatCo2, scalePower } from 'utils/formatting';

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
  const { formattingFactor, unit: powerUnit } = scalePower(netExchange);

  const unit = displayByEmissions ? __('ofCO2eqPerMinute') : powerUnit;
  const value = displayByEmissions
    ? formatCo2(Math.abs(netExchange))
    : Math.abs(round(netExchange / formattingFactor));

  return (
    <div className="w-full rounded-md bg-white p-3 shadow-xl dark:border dark:border-gray-700 dark:bg-gray-800 sm:w-[350px]">
      <AreaGraphToolTipHeader
        datetime={new Date(stateDatetime)}
        timeAverage={timeAverage}
        squareColor="#7f7f7f"
        title={__('tooltips.netExchange')}
      />
      <p className="flex justify-center text-base">
        {netExchange >= 0 ? __('tooltips.importing') : __('tooltips.exporting')}{' '}
        <b className="mx-1">{value}</b> {unit}
      </p>
    </div>
  );
}
