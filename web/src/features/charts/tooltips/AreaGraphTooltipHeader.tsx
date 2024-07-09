import EstimationBadge from 'components/EstimationBadge';
import { useGetEstimationTranslation } from 'hooks/getEstimationTranslation';
import { useTranslation } from 'react-i18next';
import { EstimationMethods, TimeAverages } from 'utils/constants';
import { formatDate } from 'utils/formatting';

import ProductionSourceIcon from '../ProductionsSourceIcons';

interface AreaGraphToolTipHeaderProps {
  squareColor: string;
  datetime: Date;
  timeAverage: TimeAverages;
  title: string;
  hasEstimationPill?: boolean;
  estimatedPercentage?: number;
  productionSource?: string;
  estimationMethod?: EstimationMethods;
}

export default function AreaGraphToolTipHeader(props: AreaGraphToolTipHeaderProps) {
  const {
    squareColor,
    datetime,
    timeAverage,
    title,
    hasEstimationPill = false,
    estimatedPercentage,
    productionSource,
    estimationMethod,
  } = props;
  const { i18n } = useTranslation();
  const pillText = useGetEstimationTranslation(
    'pill',
    estimationMethod,
    estimatedPercentage
  );
  return (
    <>
      <div className="flex justify-between">
        <div className="inline-flex items-center gap-x-1 font-bold">
          <div
            style={{
              backgroundColor: squareColor,
              height: 16,
              width: 16,
            }}
            className="rounded-sm  font-bold"
          >
            {productionSource && (
              <div className="flex h-4 w-4 justify-center pt-[3px]">
                <ProductionSourceIcon source={productionSource} />
              </div>
            )}
          </div>
          <p className="px-1 text-base">{title}</p>
        </div>
        <div className="inline-flex items-center gap-x-2">
          {hasEstimationPill && estimatedPercentage !== 0 && (
            <EstimationBadge text={pillText} />
          )}
        </div>
      </div>
      <p className="whitespace-nowrap text-sm">
        {formatDate(datetime, i18n.language, timeAverage)}
      </p>
      <hr className="my-1 mb-3 dark:border-gray-600" />
    </>
  );
}
