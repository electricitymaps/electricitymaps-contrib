import { useAtom } from 'jotai';
import { PulseLoader } from 'react-spinners';
import { useTranslation } from 'translation/translation';
import { TimeAverages } from 'utils/constants';
import { displayByEmissionsAtom } from 'utils/state/atoms';
import { useRefWidthHeightObserver } from 'utils/viewport';
import useBarBreakdownChartData from '../hooks/useBarBreakdownProductionChartData';
import BarBreakdownEmissionsChart from './BarBreakdownEmissionsChart';
import BarBreakdownProductionChart from './BarBreakdownProductionChart';

function BarBreakdownChart({ timeAverage }: { timeAverage: TimeAverages }) {
  const {
    currentZoneDetail,
    zoneDetails,
    productionData,
    exchangeData,
    isLoading,
    height,
  } = useBarBreakdownChartData();
  const [displayByEmissions] = useAtom(displayByEmissionsAtom);
  const { ref, width } = useRefWidthHeightObserver();
  const { __ } = useTranslation();

  if (isLoading || !currentZoneDetail) {
    // TODO: Replace with skeleton graph (maybe full graph with no data?)
    return <PulseLoader />;
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
    <div className="relative w-full text-md" ref={ref}>
      <div className="relative top-2 mb-1 text-sm">
        {__(
          timeAverage !== TimeAverages.HOURLY
            ? 'country-panel.averagebysource'
            : 'country-panel.bysource'
        )}
      </div>

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
