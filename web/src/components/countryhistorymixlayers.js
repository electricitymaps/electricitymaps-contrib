import React from 'react';
import { connect } from 'react-redux';

import AreaGraphLayers from './graph/areagraphlayers';

const mapStateToProps = state => ({
  displayByEmissions: state.application.tableDisplayEmissions,
  isMobile: state.application.isMobile,
});

const CountryHistoryMixLayers = React.memo(({
  displayByEmissions,
  fillColor,
  stackKeys,
  stackedData,
  timeScale,
  valueScale,
  setSelectedLayerIndex,
  mouseMoveHandler,
  mouseOutHandler,
  layerMouseMoveHandler,
  layerMouseOutHandler,
  isMobile,
  svgRef,
}) => {
  const fill = ind => fillColor(stackKeys[ind], displayByEmissions);
  const layers = stackKeys.map((key, ind) => ({ key, data: stackedData[ind] }));
  return (
    <AreaGraphLayers
      fillColor={fill}
      layers={layers}
      timeScale={timeScale}
      valueScale={valueScale}
      setSelectedLayerIndex={setSelectedLayerIndex}
      mouseMoveHandler={mouseMoveHandler}
      mouseOutHandler={mouseOutHandler}
      layerMouseMoveHandler={layerMouseMoveHandler}
      layerMouseOutHandler={layerMouseOutHandler}
      isMobile={isMobile}
      svgRef={svgRef}
    />
  );
});

export default connect(mapStateToProps)(CountryHistoryMixLayers);
