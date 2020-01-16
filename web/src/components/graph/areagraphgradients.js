import React from 'react';

const AreaGraphGradients = React.memo(({
  id,
  gradientKeys,
  graphData,
  timeScale,
  stopColor,
}) => {
  const [x1, x2] = timeScale.range();
  if (x1 >= x2) return null;

  const stopOffset = datetime => `${(timeScale(datetime) - x1) / (x2 - x1) * 100.0}%`;

  return (
    <React.Fragment>
      {gradientKeys.map(key => (
        <linearGradient gradientUnits="userSpaceOnUse" id={`${id}-${key}`} key={key} x1={x1} x2={x2}>
          {graphData.map(datapoint => (
            <stop
              key={datapoint.datetime}
              offset={stopOffset(datapoint.datetime)}
              stopColor={stopColor(datapoint, key)}
            />
          ))}
        </linearGradient>
      ))}
    </React.Fragment>
  );
});

export default AreaGraphGradients;
