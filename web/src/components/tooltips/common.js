import React from 'react';
import { isFinite } from 'lodash';

import { getFullZoneName } from '../../helpers/translation';
import { getCo2Scale } from '../../helpers/scales';
import { flagUri } from '../../helpers/flags';

export const CarbonIntensity = ({ colorBlindModeEnabled, intensity }) => {
  const co2ColorScale = getCo2Scale(colorBlindModeEnabled);
  return (
    <React.Fragment>
      <div className="emission-rect" style={{ backgroundColor: co2ColorScale(intensity) }} />
      {' '}
      <b>{Math.round(intensity) || '?'}</b> gCO<span className="sub">2</span>eq/kWh
    </React.Fragment>
  );
};

export const MetricRatio = ({ value, total, format }) => (
  <small
    dangerouslySetInnerHTML={{
      __html: `(${isFinite(value) ? format(value) : '?'} / ${isFinite(total) ? format(total) : '?'})`,
    }}
  />
);

export const ZoneName = ({ zone }) => (
  <React.Fragment>
    <img className="flag" alt="" src={flagUri(zone)} /> {getFullZoneName(zone)}
  </React.Fragment>
);
