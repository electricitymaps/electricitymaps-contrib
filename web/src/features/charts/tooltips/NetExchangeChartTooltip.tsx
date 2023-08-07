import { useAtom } from 'jotai';
import { useTranslation } from 'translation/translation';
import { timeAverageAtom } from 'utils/state/atoms';
import { InnerAreaGraphTooltipProps } from '../types';
import AreaGraphToolTipHeader from './AreaGraphTooltipHeader';
import { getNetExchange, round } from 'utils/helpers';
import { scalePower } from 'utils/formatting';

export default function NetExchangeChartTooltip({
  zoneDetail,
}: InnerAreaGraphTooltipProps) {
  const [timeAverage] = useAtom(timeAverageAtom);
  const { __ } = useTranslation();

  if (!zoneDetail) {
    return null;
  }
  const { stateDatetime } = zoneDetail;

  const netExchange = getNetExchange(zoneDetail);
  const { formattingFactor, unit } = scalePower(netExchange);

  return (
    <div className="w-max rounded-md bg-white p-3 shadow-xl dark:bg-gray-900">
      <AreaGraphToolTipHeader
        datetime={new Date(stateDatetime)}
        timeAverage={timeAverage}
        squareColor="#7f7f7f"
        title={__('tooltips.netExchange')}
      />
      <p className="flex justify-center text-base">
        {netExchange >= 0 ? __('tooltips.importing') : __('tooltips.exporting')}{' '}
        {Math.abs(round(netExchange / formattingFactor))} {unit}
      </p>
    </div>
  );
}
