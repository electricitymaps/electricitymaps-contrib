import { useAtomValue } from 'jotai';
import { ElectricityModeType } from 'types';
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

  if (!zoneDetail || !selectedLayerKey) {
    return null;
  }

  // If layer key is not a generation type, it is an exchange
  const isExchange = !getGenerationTypeKey(selectedLayerKey);

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

  return Number.isFinite(shownValue) ? (
    <BreakdownChartTooltipContent
      {...contentData}
      datetime={date}
      isExchange={isExchange}
      selectedLayerKey={selectedLayerKey}
      timeRange={timeRange}
      hasEstimationPill={hasEstimationPill}
      estimatedPercentage={roundedEstimatedPercentage}
      estimationMethod={estimationMethod}
    />
  ) : (
    <BreakdownChartTooltipContentNoData
      datetime={date}
      isExchange={isExchange}
      selectedLayerKey={selectedLayerKey}
      timeRange={timeRange}
    />
  );
}
