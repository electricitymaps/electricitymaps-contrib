import React from 'react';

import { getCo2Scale } from '../../helpers/scales';

const ExchangeLinearGradients = React.memo(({
  colorBlindModeEnabled,
  exchangeKeys,
  graphData,
  timeScale,
}) => {
  const [x1, x2] = timeScale.range();
  if (x1 >= x2) return null;

  const co2ColorScale = getCo2Scale(colorBlindModeEnabled);
  const stopOffset = datetime => `${(timeScale(datetime) - x1) / (x2 - x1) * 100.0}%`;
  const stopColor = (countryData, key) => (countryData.exchangeCo2Intensities
    ? co2ColorScale(countryData.exchangeCo2Intensities[key]) : 'darkgray');

  return (
    <React.Fragment>
      {exchangeKeys.map(key => (
        <linearGradient gradientUnits="userSpaceOnUse" id={`areagraph-exchange-${key}`} key={key} x1={x1} x2={x2}>
          {graphData.map(d => (
            <stop
              key={d.datetime}
              offset={stopOffset(d.datetime)}
              stopColor={stopColor(d._countryData, key)}
            />
          ))}
        </linearGradient>
      ))}
    </React.Fragment>
  );
});

export default ExchangeLinearGradients;
