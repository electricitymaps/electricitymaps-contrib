import { useAtom } from 'jotai';
import { useTranslation } from 'translation/translation';
import { displayByEmissionsAtom } from 'utils/state/atoms';
import { useReferenceWidthHeightObserver } from 'utils/viewport';
import useBarBreakdownChartData from '../hooks/useBarBreakdownProductionChartData';
import BarBreakdownEmissionsChart from './BarBreakdownEmissionsChart';
import BarBreakdownProductionChart from './BarBreakdownProductionChart';
import BySource from './BySource';
import EmptyBarBreakdownChart from './EmptyBarBreakdownChart';

function BarBreakdownChart() {
  const {
    currentZoneDetail,
    zoneDetails,
    productionData,
    exchangeData,
    isLoading,
    height,
  } = useBarBreakdownChartData();
  const [displayByEmissions] = useAtom(displayByEmissionsAtom);
  const { ref, width } = useReferenceWidthHeightObserver();
  const { __ } = useTranslation();

  if (isLoading) {
    return null;
  }

  if (!currentZoneDetail) {
    return (
      <div className="relative w-full text-md" ref={ref}>
        <BySource className="opacity-40" />
        <EmptyBarBreakdownChart
          height={height}
          width={width}
          overLayText={__('country-panel.noDataAtTimestamp')}
        />
      </div>
    );
  }

  // TODO: Show CountryTableOverlayIfNoData when required

  const todoHandler = () => {
    console.warn('TODO: Handle tooltips');
    // see countrytable.jsx
    // handleProductionRowMouseOver
    //handleProductionRowMouseOut
    //handleExchangeRowMouseOver
    //handleExchangeRowMouseOut
  };

  return (
    <div className="relative w-full text-md " ref={ref}>
      <BySource />
      {displayByEmissions ? (
        <BarBreakdownEmissionsChart
          data={currentZoneDetail}
          productionData={productionData}
          exchangeData={exchangeData}
          onProductionRowMouseOver={todoHandler}
          onProductionRowMouseOut={todoHandler}
          onExchangeRowMouseOver={todoHandler}
          onExchangeRowMouseOut={todoHandler}
          width={width}
          height={height}
          isMobile={false}
        />
      ) : (
        <BarBreakdownProductionChart
          data={zoneDetails}
          currentData={currentZoneDetail}
          productionData={productionData}
          exchangeData={exchangeData}
          onProductionRowMouseOver={todoHandler}
          onProductionRowMouseOut={todoHandler}
          onExchangeRowMouseOver={todoHandler}
          onExchangeRowMouseOut={todoHandler}
          width={width}
          height={height}
          isMobile={false}
        />
      )}
    </div>
  );
}

export default BarBreakdownChart;
