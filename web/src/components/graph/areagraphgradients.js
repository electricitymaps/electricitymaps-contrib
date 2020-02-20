import React from 'react';

const AreaGraphGradients = React.memo(({
  id,
  layers,
  timeScale,
  stopColorSelector,
}) => {
  const [x1, x2] = timeScale.range();
  if (x1 >= x2) return null;

  const stopOffset = datetime => `${(timeScale(datetime) - x1) / (x2 - x1) * 100.0}%`;

  return (
    <React.Fragment>
      {layers.map(layer => (
        <linearGradient gradientUnits="userSpaceOnUse" id={`${id}-${layer.key}`} key={layer.key} x1={x1} x2={x2}>
          {layer.data.map(({ data }) => (
            <stop
              key={data.datetime}
              offset={stopOffset(data.datetime)}
              stopColor={stopColorSelector(data, layer.key)}
            />
          ))}
        </linearGradient>
      ))}
    </React.Fragment>
  );
});

export default AreaGraphGradients;
