import { HorizontalDivider } from 'components/Divider';
import EstimationBadge from 'components/EstimationBadge';
import { FormattedTime } from 'components/Time';
import { useGetEstimationTranslation } from 'hooks/getEstimationTranslation';
import { CircleDashed, TrendingUpDown } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { EstimationMethods } from 'utils/constants';

import ProductionSourceIcon from '../ProductionsSourceIcons';

interface AreaGraphToolTipHeaderProps {
  squareColor: string;
  datetime: Date;
  title: string;
  hasEstimationPill?: boolean;
  estimatedPercentage?: number;
  productionSource?: string;
  estimationMethod?: EstimationMethods;
}

export default function AreaGraphToolTipHeader({
  squareColor,
  datetime,
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
            Icon={
              estimationMethod === EstimationMethods.TSA ? CircleDashed : TrendingUpDown
            }
          />
        )}
      </div>
      <FormattedTime
        datetime={datetime}
        language={i18n.languages[0]}
        className="text-sm"
      />
      <HorizontalDivider />
    </>
  );
}
