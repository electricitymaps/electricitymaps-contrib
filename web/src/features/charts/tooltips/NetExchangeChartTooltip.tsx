import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { formatCo2, scalePower } from 'utils/formatting';
import { getNetExchange, round } from 'utils/helpers';
import { displayByEmissionsAtom, isHourlyAtom, timeRangeAtom } from 'utils/state/atoms';

import { InnerAreaGraphTooltipProps } from '../types';
import AreaGraphToolTipHeader from './AreaGraphTooltipHeader';

export default function NetExchangeChartTooltip({
  zoneDetail,
}: InnerAreaGraphTooltipProps) {
  const timeRange = useAtomValue(timeRangeAtom);
  const displayByEmissions = useAtomValue(displayByEmissionsAtom);
  const isHourly = useAtomValue(isHourlyAtom);
  const { t } = useTranslation();

  if (!zoneDetail) {
    return null;
  }

  const { stateDatetime } = zoneDetail;

  const netExchange = getNetExchange(zoneDetail, displayByEmissions);
  const { formattingFactor, unit: powerUnit } = scalePower(netExchange, isHourly);

  const unit = displayByEmissions ? t('ofCO2eq') : powerUnit;
  const value = displayByEmissions
    ? formatCo2({ value: Math.abs(netExchange) })
    : Math.abs(round(netExchange / formattingFactor));

  return (
    <div className="w-full rounded-md bg-white p-3 shadow-xl dark:border dark:border-neutral-700 dark:bg-neutral-800 sm:w-[350px]">
      <AreaGraphToolTipHeader
        datetime={new Date(stateDatetime)}
        timeRange={timeRange}
        squareColor="#7f7f7f"
        title={t('tooltips.netExchange')}
      />
      <p className="flex justify-center text-base">
        {netExchange >= 0 ? t('tooltips.importing') : t('tooltips.exporting')}{' '}
        <b className="mx-1">{Number.isFinite(value) ? value : '?'}</b> {unit}
      </p>
    </div>
  );
}
