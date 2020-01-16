import React from 'react';
import { connect } from 'react-redux';

import { getCo2Scale } from '../helpers/scales';

import AreaGraphGradients from './graph/areagraphgradients';

const mapStateToProps = (state, props) => ({
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
});

const CountryHistoryExchangeGradients = React.memo(({
  colorBlindModeEnabled,
  exchangeKeys,
  graphData,
  timeScale,
}) => {
  const co2ColorScale = getCo2Scale(colorBlindModeEnabled);
  const stopColor = (d, key) => (d._countryData.exchangeCo2Intensities
    ? co2ColorScale(d._countryData.exchangeCo2Intensities[key]) : 'darkgray');

  return (
    <AreaGraphGradients
      id="areagraph-exchange"
      gradientKeys={exchangeKeys}
      graphData={graphData}
      timeScale={timeScale}
      stopColor={stopColor}
    />
  );
});

export default connect(mapStateToProps)(CountryHistoryExchangeGradients);
