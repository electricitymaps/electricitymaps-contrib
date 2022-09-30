/* eslint-disable*/
import React, { useState } from 'react';
import styled from 'styled-components';
import CarbonIntensitySquare from '../../../components/carbonintensitysquare';
import { CountryLowCarbonGauge } from './countryLowCarbonGauge';
import { CountryRenewableGauge } from './countryRenewableGauge';
import { noop } from '../../../helpers/noop';
import { useTranslation } from '../../../helpers/translation';
import LowCarbonInfoTooltip from '../../../components/tooltips/lowcarboninfotooltip';
import { getCO2IntensityByMode } from '../../../helpers/zonedata';

const CountryTableHeaderInner = styled.div`
  display: flex;
  flex-basis: 33.3%;
  justify-content: space-between;
`;

export const CountryOverview = ({
  data,
  isMobile,
  switchToZoneProduction,
  switchToZoneEmissions,
  tableDisplayEmissions,
  electricityMixMode,
}) => {
  const [tooltip, setTooltip] = useState(null);
  const { __ } = useTranslation();
  const co2intensity = getCO2IntensityByMode(data, electricityMixMode);

  return (
    <React.Fragment>
      <CountryTableHeaderInner>
        <CarbonIntensitySquare value={co2intensity} withSubtext />
        <div className="country-col country-lowcarbon-wrap">
          <div id="country-lowcarbon-gauge" className="country-gauge-wrap">
            <CountryLowCarbonGauge
              onClick={isMobile ? (x, y) => setTooltip({ position: { x, y } }) : noop}
              onMouseMove={!isMobile ? (x, y) => setTooltip({ position: { x, y } }) : noop}
              onMouseOut={() => setTooltip(null)}
            />
            {tooltip && <LowCarbonInfoTooltip position={tooltip.position} onClose={() => setTooltip(null)} />}
          </div>
          <div className="country-col-headline">{__('country-panel.lowcarbon')}</div>
          <div className="country-col-subtext" />
        </div>
        <div className="country-col country-renewable-wrap">
          <div id="country-renewable-gauge" className="country-gauge-wrap">
            <CountryRenewableGauge />
          </div>
          <div className="country-col-headline">{__('country-panel.renewable')}</div>
        </div>
      </CountryTableHeaderInner>
      <div className="country-show-emissions-wrap">
        <div className="menu">
          <button type="button" onClick={switchToZoneProduction} className={!tableDisplayEmissions ? 'selected' : null}>
            {__(`country-panel.electricity${electricityMixMode}`)}
          </button>
          |
          <button type="button" onClick={switchToZoneEmissions} className={tableDisplayEmissions ? 'selected' : null}>
            {__('country-panel.emissions')}
          </button>
        </div>
      </div>
    </React.Fragment>
  );
};
