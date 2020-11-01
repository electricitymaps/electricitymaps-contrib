import React from 'react';
import { isFinite } from 'lodash';

import { getFullZoneName } from '../../helpers/translation';
import { useCo2ColorScale } from '../../hooks/theme';
import { flagUri } from '../../helpers/flags';

export const CarbonIntensity = ({ intensity }) => {
  const co2ColorScale = useCo2ColorScale();

  return (
    <React.Fragment>
      <div className="emission-rect" style={{ backgroundColor: co2ColorScale(intensity) }} />
      {' '}
      <b>{Math.round(intensity) || '?'}</b> gCO₂eq/kWh
    </React.Fragment>
  );
};

export const MetricRatio = ({ value, total, format }) => (
  <small>{`(${isFinite(value) ? format(value) : '?'} / ${isFinite(total) ? format(total) : '?'})`}</small>
);

export const ZoneName = ({ zone }) => (
  <React.Fragment>
    <img className="flag" alt="" src={flagUri(zone)} /> {getFullZoneName(zone)}
  </React.Fragment>
);
