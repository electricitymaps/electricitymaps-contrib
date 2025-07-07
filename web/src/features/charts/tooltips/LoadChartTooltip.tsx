import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { scalePower } from 'utils/formatting';
import { round } from 'utils/helpers';
import { isFiveMinuteOrHourlyGranularityAtom, timeRangeAtom } from 'utils/state/atoms';

import { InnerAreaGraphTooltipProps } from '../types';
import AreaGraphToolTipHeader from './AreaGraphTooltipHeader';

export default function LoadChartTooltip({ zoneDetail }: InnerAreaGraphTooltipProps) {
  const timeRange = useAtomValue(timeRangeAtom);
  const isFineGranularity = useAtomValue(isFiveMinuteOrHourlyGranularityAtom);
  const { t } = useTranslation();

  if (!zoneDetail) {
    return null;
  }

  const { stateDatetime, estimationMethod, estimatedPercentage } = zoneDetail;

  const totalConsumption = zoneDetail.totalConsumption;
  const { formattingFactor, unit: powerUnit } = scalePower(
    totalConsumption,
    isFineGranularity
  );

  const unit = powerUnit;
  const value = round(totalConsumption / formattingFactor);
  const roundedEstimatedPercentage = round(estimatedPercentage ?? 0, 0);
  const hasEstimationOrAggregationPill = Boolean(estimationMethod) || !isFineGranularity;

  return (
    <div className="w-full rounded-md bg-white p-3 shadow-xl dark:border dark:border-neutral-700 dark:bg-neutral-800 sm:w-[350px]">
      <AreaGraphToolTipHeader
        datetime={new Date(stateDatetime)}
        timeRange={timeRange}
        squareColor="#7f7f7f"
        title={t('tooltips.load')}
        hasEstimationOrAggregationPill={hasEstimationOrAggregationPill}
        estimatedPercentage={roundedEstimatedPercentage}
        estimationMethod={estimationMethod}
      />
      <p className="flex justify-center text-base">
        <b className="mx-1">{Number.isFinite(value) ? value : '?'}</b> {unit}
      </p>
    </div>
  );
}
