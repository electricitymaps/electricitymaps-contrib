import getSymbolFromCurrency from 'currency-symbol-map';
import { useAtom } from 'jotai';
import AreaGraphToolTipHeader from 'stories/tooltips/AreaGraphTooltipHeader';
import { useTranslation } from 'translation/translation';
import { timeAverageAtom } from 'utils/state/atoms';
import { InnerAreaGraphTooltipProps } from '../types';

export default function PriceChartTooltip(props: InnerAreaGraphTooltipProps) {
  const { zoneDetail } = props;
  const [timeAverage] = useAtom(timeAverageAtom);
  const { __ } = useTranslation();

  const { price, stateDatetime } = zoneDetail;

  const priceIsDefined = price && typeof price.value === 'number';
  const currency = priceIsDefined ? getSymbolFromCurrency(price?.currency) : '?';
  const value = priceIsDefined ? price?.value : '';

  return (
    <div className="w-[250px] rounded-md bg-white p-3 shadow-xl">
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
