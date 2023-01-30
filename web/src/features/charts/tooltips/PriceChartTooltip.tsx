import getSymbolFromCurrency from 'currency-symbol-map';
import { useAtom } from 'jotai';
import { useTranslation } from 'translation/translation';
import { timeAverageAtom } from 'utils/state/atoms';
import { InnerAreaGraphTooltipProps } from '../types';
import AreaGraphToolTipHeader from './AreaGraphTooltipHeader';

export default function PriceChartTooltip({ zoneDetail }: InnerAreaGraphTooltipProps) {
  const [timeAverage] = useAtom(timeAverageAtom);
  const { __ } = useTranslation();

  if (!zoneDetail) {
    return null;
  }
  const { price, stateDatetime } = zoneDetail;

  const priceIsDefined = price && typeof price.value === 'number';
  const currency = priceIsDefined ? getSymbolFromCurrency(price?.currency) : '?';
  const value = priceIsDefined ? price?.value : '';

  return (
    <div className="w-full rounded-md bg-white p-3 shadow-xl dark:bg-gray-900 sm:w-64">
      <AreaGraphToolTipHeader
        datetime={new Date(stateDatetime)}
        timeAverage={timeAverage}
        squareColor="#7f7f7f" // TODO: use price scale color
        title={__('tooltips.price')} // TODO: get from translation
      />
      <p className="flex justify-center text-base">
        <b className="mr-1">{value}</b>
        {currency} / MWh
      </p>
    </div>
  );
}
