import EstimationBadge from 'components/EstimationBadge';
import HorizontalDivider from 'components/HorizontalDivider';
import { FormattedTime } from 'components/Time';
import { useGetEstimationTranslation } from 'hooks/getEstimationTranslation';
import { useAtomValue } from 'jotai';
import { CircleDashed, TrendingUpDown } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { EstimationMethods, isTSAModel, TimeRange } from 'utils/constants';
import { endDatetimeAtom } from 'utils/state/atoms';

import ProductionSourceIcon from '../ProductionsSourceIcons';

interface AreaGraphToolTipHeaderProps {
  squareColor: string;
  datetime: Date;
  timeRange: TimeRange;
  title: string;
  hasEstimationPill?: boolean;
  estimatedPercentage?: number;
  productionSource?: string;
  estimationMethod?: EstimationMethods;
}

export default function AreaGraphToolTipHeader({
  squareColor,
  datetime,
  timeRange,
  title,
  hasEstimationPill = false,
  estimatedPercentage,
  productionSource,
  estimationMethod,
}: AreaGraphToolTipHeaderProps) {
  const { i18n } = useTranslation();
  const pillText = useGetEstimationTranslation(
    'pill',
    estimationMethod,
    estimatedPercentage
  );
  const endDatetime = useAtomValue(endDatetimeAtom);
  const isTSA = isTSAModel(estimationMethod);
  return (
    <>
      <div className="flex items-center gap-1 font-bold">
        <div
          style={{
            backgroundColor: squareColor,
          }}
          className="flex h-4 w-4 items-center justify-center rounded-sm"
        >
          {productionSource && <ProductionSourceIcon source={productionSource} />}
        </div>
        <h2 className="grow px-1">{title}</h2>
        {hasEstimationPill && (
          <EstimationBadge
            text={pillText}
            Icon={isTSA ? CircleDashed : TrendingUpDown}
            isPreliminary={isTSA}
          />
        )}
      </div>
      <FormattedTime
        endDatetime={endDatetime}
        datetime={datetime}
        language={i18n.languages[0]}
        timeRange={timeRange}
        className="text-sm"
      />
      <HorizontalDivider />
    </>
  );
}
