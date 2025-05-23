import GlassContainer from 'components/GlassContainer';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { getZoneName } from 'translation/translation';
import { ElectricityModeType } from 'types';
import { modeColor } from 'utils/constants';
import { round } from 'utils/helpers';
import {
  displayByEmissionsAtom,
  isConsumptionAtom,
  timeRangeAtom,
} from 'utils/state/atoms';

import { getGenerationTypeKey } from '../graphUtils';
import {
  ExchangeTooltipData,
  getExchangeTooltipData,
  getProductionTooltipData,
  ProductionTooltipData,
} from '../tooltipCalculations';
import { InnerAreaGraphTooltipProps } from '../types';
import AreaGraphToolTipHeader from './AreaGraphTooltipHeader';
import {
  BreakdownChartTooltipContent,
  BreakdownChartTooltipContentNoData,
} from './BreakdownChatTooltipContent';

// Type guard function
function isExchangeTooltipData(
  data: ExchangeTooltipData | ProductionTooltipData
): data is ExchangeTooltipData {
  return 'usage' in data && !('production' in data);
}

export default function BreakdownChartTooltip({
  zoneDetail,
  selectedLayerKey,
}: InnerAreaGraphTooltipProps) {
  const displayByEmissions = useAtomValue(displayByEmissionsAtom);
  const timeRange = useAtomValue(timeRangeAtom);
  const isConsumption = useAtomValue(isConsumptionAtom);
  const co2ColorScale = useCo2ColorScale();
  const { t } = useTranslation();

  if (!zoneDetail || !selectedLayerKey) {
    return null;
  }

  // If layer key is not a generation type, it is an exchange
  const isExchange = !getGenerationTypeKey(selectedLayerKey);

  const title = isExchange
    ? getZoneName(selectedLayerKey)
    : t(selectedLayerKey).charAt(0).toUpperCase() + t(selectedLayerKey).slice(1);

  const contentData = isExchange
    ? getExchangeTooltipData(selectedLayerKey, zoneDetail, displayByEmissions)
    : getProductionTooltipData(
        selectedLayerKey as ElectricityModeType,
        zoneDetail,
        displayByEmissions,
        isConsumption
      );

  const { estimationMethod, stateDatetime, estimatedPercentage } = zoneDetail;
  const roundedEstimatedPercentage = round(estimatedPercentage ?? 0, 0);
  const hasEstimationPill =
    estimationMethod != undefined || Boolean(roundedEstimatedPercentage);

  const date = new Date(stateDatetime);

  const shownValue = isExchangeTooltipData(contentData)
    ? contentData.usage
    : contentData.production;

  const isValidValue = Number.isFinite(shownValue);
  return (
    <GlassContainer className="w-full rounded-md bg-white p-3 text-sm shadow-3xl dark:border dark:border-neutral-700 dark:bg-neutral-800 sm:w-[410px]">
      <AreaGraphToolTipHeader
        squareColor={
          isExchange
            ? co2ColorScale(contentData.co2Intensity ?? Number.NaN)
            : modeColor[selectedLayerKey as ElectricityModeType]
        }
        datetime={date}
        timeRange={timeRange}
        title={title}
        hasEstimationPill={!isValidValue || isExchange ? false : hasEstimationPill}
        estimatedPercentage={estimatedPercentage}
        productionSource={isExchange ? undefined : selectedLayerKey}
        estimationMethod={estimationMethod}
      />
      {isValidValue ? (
        <BreakdownChartTooltipContent
          {...contentData}
          isExchange={isExchange}
          selectedLayerKey={selectedLayerKey}
        />
      ) : (
        <BreakdownChartTooltipContentNoData isExchange={isExchange} />
      )}
    </GlassContainer>
  );
}
