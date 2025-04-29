import useGetZone from 'api/getZone'; // Assuming zone data comes from here
import { FormattedTime } from 'components/Time'; // Use FormattedTime
// For tooltip
import { sum } from 'd3-array';
import { useAtomValue } from 'jotai';
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { ElectricityModeType } from 'types';
import { Charts, TimeRange } from 'utils/constants';
import { formatPower, scalePower } from 'utils/formatting';
import { isHourlyAtom } from 'utils/state/atoms';

import { ChartSubtitle, ChartTitle } from './ChartTitle';
import AreaGraph from './elements/AreaGraph';
import { getGenerationTypeKey, noop } from './graphUtils';
import { NotEnoughDataMessage } from './NotEnoughDataMessage';
import { RoundedCard } from './RoundedCard';
import { AreaGraphElement, InnerAreaGraphTooltipProps } from './types';

// Define layer fill using a standard function to satisfy linter and type
function layerFill(key: string): (d: { data: AreaGraphElement }) => string {
  // key and d are ignored as the color is constant for LoadChart
  return (d: { data: AreaGraphElement }) => '#808080';
}

interface LoadChartProps {
  datetimes: Date[];
  timeRange: TimeRange;
}

// Simple Tooltip Component
interface LoadTooltipProps extends InnerAreaGraphTooltipProps {
  datapoint?: AreaGraphElement | null;
  valueAxisLabel: string;
  language: string; // Pass language as prop
}

function LoadTooltip({ datapoint, valueAxisLabel, language, ...rest }: LoadTooltipProps) {
  if (!datapoint) {
    return null;
  }

  const totalLoad =
    typeof datapoint.layerData?.load === 'number' ? datapoint.layerData.load : 0;

  return (
    <div className="text-center text-xs" {...rest}>
      <FormattedTime
        datetime={datapoint.datetime}
        language={language}
        className="font-bold"
      />
      <div>
        <span className="font-bold">{formatPower({ value: totalLoad })}</span>
        {` ${valueAxisLabel}`}
      </div>
    </div>
  );
}

// Simplified hook to fetch and process data for LoadChart
function useLoadChartData() {
  const { data: zoneData, isLoading, isError } = useGetZone();
  const isHourly = useAtomValue(isHourlyAtom);

  const processedData = useMemo(() => {
    if (
      isLoading ||
      isError ||
      !zoneData ||
      !zoneData.zoneStates ||
      Object.keys(zoneData.zoneStates).length === 0
    ) {
      return null;
    }

    const productionValues = Object.values(zoneData.zoneStates)
      .map((d) =>
        d?.production
          ? sum(
              Object.values(d.production).filter(
                (v): v is number => typeof v === 'number' && !Number.isNaN(v)
              )
            )
          : 0
      )
      .filter((v): v is number => typeof v === 'number' && !Number.isNaN(v));

    const maxTotalProduction =
      productionValues.length > 0 ? Math.max(0, ...productionValues) : 0;

    const { formattingFactor, unit } = scalePower(maxTotalProduction, isHourly);
    const valueAxisLabel = unit;

    const chartData: AreaGraphElement[] = [];

    for (const [datetimeString, value] of Object.entries(zoneData.zoneStates)) {
      if (!value || !value.production) {
        continue;
      }

      const datetime = new Date(datetimeString);
      let totalProduction = 0;

      for (const [mode, productionValue] of Object.entries(value.production)) {
        if (typeof productionValue === 'number' && !Number.isNaN(productionValue)) {
          const generationKey = getGenerationTypeKey(mode as ElectricityModeType);
          if (generationKey) {
            totalProduction += productionValue;
          }
        }
      }

      const scaledTotalProduction =
        formattingFactor === 0 ? 0 : totalProduction / formattingFactor;

      chartData.push({
        datetime,
        meta: value,
        layerData: { load: scaledTotalProduction },
      });
    }

    return {
      chartData,
      valueAxisLabel,
      isLoading: false,
      isError: false,
    };
  }, [zoneData, isLoading, isError, isHourly]);

  return processedData;
}

// Factory function to create the tooltip component with required props
const createLoadTooltipComponent = (valueAxisLabel: string, language: string) => {
  // Define the component function returned by the factory
  function MemoizedLoadTooltip(
    props: InnerAreaGraphTooltipProps & { datapoint?: AreaGraphElement | null }
  ) {
    return <LoadTooltip {...props} valueAxisLabel={valueAxisLabel} language={language} />;
  }
  // Add display name for DevTools and linting
  MemoizedLoadTooltip.displayName = 'MemoizedLoadTooltip';
  return MemoizedLoadTooltip;
};

export default function LoadChart({ datetimes, timeRange }: LoadChartProps) {
  const { t, i18n } = useTranslation(); // Get i18n object
  const language = i18n.language; // Get current language
  const data = useLoadChartData();
  const valueAxisLabel = data?.valueAxisLabel || ''; // Get label safely

  // Use the factory function within useMemo to create the tooltip component instance.
  // This ensures the component identity is stable across renders unless props change.
  const TooltipComponent = useMemo(
    () => createLoadTooltipComponent(valueAxisLabel, language),
    [valueAxisLabel, language]
  );

  if (!data) {
    return (
      <RoundedCard>
        <div>Loading Chart...</div>
      </RoundedCard>
    );
  }

  const { chartData, isLoading, isError } = data; // Remove valueAxisLabel here as it's derived above

  if (isLoading) {
    return (
      <RoundedCard>
        <div>Loading Chart Data...</div>
      </RoundedCard>
    );
  }

  if (isError || !chartData || chartData.length < 2) {
    return (
      <NotEnoughDataMessage
        id={Charts.LOAD_CHART}
        title={t(`country-history.load.${timeRange}`, 'Electricity Load')}
      />
    );
  }

  return (
    <RoundedCard>
      <ChartTitle
        titleText={t(`country-history.load.${timeRange}`, 'Electricity Load')}
        unit={valueAxisLabel} // Use the derived valueAxisLabel
        id={Charts.LOAD_CHART}
        subtitle={<ChartSubtitle datetimes={datetimes} timeRange={timeRange} />}
      />
      <div className="relative ">
        <AreaGraph
          testId="history-load-graph"
          isDataInteractive={true}
          data={chartData}
          layerKeys={['load']}
          layerFill={layerFill} // Pass the standard function directly
          markerUpdateHandler={noop}
          markerHideHandler={noop}
          height="10em"
          datetimes={datetimes}
          selectedTimeRange={timeRange}
          tooltip={TooltipComponent} // Pass the memoized component
        />
      </div>
    </RoundedCard>
  );
}
