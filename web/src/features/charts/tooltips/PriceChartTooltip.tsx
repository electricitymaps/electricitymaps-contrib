import getSymbolFromCurrency from 'currency-symbol-map';
import { useAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { timeAverageAtom } from 'utils/state/atoms';
import { EnergyUnits } from 'utils/units';

import { InnerAreaGraphTooltipProps } from '../types';
import AreaGraphToolTipHeader from './AreaGraphTooltipHeader';

export default function PriceChartTooltip({ zoneDetail }: InnerAreaGraphTooltipProps) {
  const [timeAverage] = useAtom(timeAverageAtom);
  const { t } = useTranslation();

  if (!zoneDetail) {
    return null;
  }
  const { price, stateDatetime } = zoneDetail;

  const priceIsDefined = typeof price?.value === 'number';
  const currency = priceIsDefined ? getSymbolFromCurrency(price?.currency) : '?';
  const value = priceIsDefined ? price?.value : '';

  return (
    <div className="w-full rounded-md bg-white p-3 shadow-xl sm:w-64 dark:border dark:border-gray-700  dark:bg-gray-800">
      <AreaGraphToolTipHeader
        datetime={new Date(stateDatetime)}
        timeAverage={timeAverage}
        squareColor="#7f7f7f" // TODO: use price scale color
        title={t('tooltips.price')} // TODO: get from translation
      />
      <p className="flex justify-center text-base">
        <b className="mr-1">{value}</b>
        {currency} / {EnergyUnits.MEGAWATT_HOURS}
      </p>
    </div>
  );
}
