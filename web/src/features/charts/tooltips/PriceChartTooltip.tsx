import getSymbolFromCurrency from 'currency-symbol-map';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { timeRangeAtom } from 'utils/state/atoms';

import { convertPrice } from '../bar-breakdown/utils';
import { InnerAreaGraphTooltipProps } from '../types';
import AreaGraphToolTipHeader from './AreaGraphTooltipHeader';

export default function PriceChartTooltip({ zoneDetail }: InnerAreaGraphTooltipProps) {
  const timeRange = useAtomValue(timeRangeAtom);
  const { t } = useTranslation();

  if (!zoneDetail) {
    return null;
  }
  const { price: priceObject, stateDatetime } = zoneDetail;
  const { value, currency, unit } = convertPrice(
    priceObject?.value,
    priceObject?.currency
  );
  const currencySymbol = getSymbolFromCurrency(currency) ?? '?';
  const price = Number.isFinite(value) ? value : '?';

  return (
    <div className="w-full rounded-md bg-white p-3 shadow-xl dark:border dark:border-neutral-700 dark:bg-neutral-800 sm:w-64">
      <AreaGraphToolTipHeader
        datetime={new Date(stateDatetime)}
        timeRange={timeRange}
        squareColor="#7f7f7f" // TODO: use price scale color
        title={t('tooltips.price')}
      />
      <p className="flex justify-center text-base">
        <b className="mr-1">{price}</b>
        {currencySymbol} / {unit}
      </p>
    </div>
  );
}
