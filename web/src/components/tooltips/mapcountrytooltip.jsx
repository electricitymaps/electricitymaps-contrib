import React from 'react';
import { connect } from 'react-redux';

import { useTranslation } from '../../helpers/translation';
import styled from 'styled-components';

import CircularGauge from '../circulargauge';
import CarbonIntensitySquare from '../carbonintensitysquare';
import Tooltip from '../tooltip';
import { ZoneName } from './common';

const mapStateToProps = (state) => ({
  electricityMixMode: state.application.electricityMixMode,
});

const CountryTableHeaderInner = styled.div`
  display: flex;
  flex-basis: 33.3%;
  justify-content: space-between;
`;

const TooltipContent = React.memo(
  ({ isDataDelayed, hasData, co2intensity, fossilFuelPercentage, renewablePercentage }) => {
    const { __ } = useTranslation();
    if (!hasData) {
      return (
        <div className="no-parser-text">
          <span
            dangerouslySetInnerHTML={{
              __html: __(
                'tooltips.noParserInfo',
                'https://github.com/tmrowco/electricitymap-contrib/wiki/Getting-started'
              ),
            }}
          />
        </div>
      );
    }
    if (!co2intensity) {
      if (isDataDelayed) {
        return <div className="temporary-outage-text">{__('tooltips.dataIsDelayed')}</div>;
      }
      return <div className="temporary-outage-text">{__('tooltips.temporaryDataOutage')}</div>;
    }
    return (
      <div className="zone-details">
        <CountryTableHeaderInner>
          <CarbonIntensitySquare value={co2intensity} />
          <div className="country-col country-lowcarbon-wrap">
            <div id="tooltip-country-lowcarbon-gauge" className="country-gauge-wrap">
              <CircularGauge percentage={fossilFuelPercentage} />
            </div>
            <div className="country-col-headline">{__('country-panel.lowcarbon')}</div>
            <div className="country-col-subtext" />
          </div>
          <div className="country-col country-renewable-wrap">
            <div id="tooltip-country-renewable-gauge" className="country-gauge-wrap">
              <CircularGauge percentage={renewablePercentage} />
            </div>
            <div className="country-col-headline">{__('country-panel.renewable')}</div>
          </div>
        </CountryTableHeaderInner>
      </div>
    );
  }
);

const MapCountryTooltip = ({ electricityMixMode, position, zoneData, onClose }) => {
  if (!zoneData) {
    return null;
  }

  const isDataDelayed = zoneData.delays && zoneData.delays.production;

  const co2intensity = electricityMixMode === 'consumption' ? zoneData.co2intensity : zoneData.co2intensityProduction;

  const fossilFuelRatio =
    electricityMixMode === 'consumption' ? zoneData.fossilFuelRatio : zoneData.fossilFuelRatioProduction;
  const fossilFuelPercentage = fossilFuelRatio !== null ? Math.round(100 * (1 - fossilFuelRatio)) : '?';

  const renewableRatio =
    electricityMixMode === 'consumption' ? zoneData.renewableRatio : zoneData.renewableRatioProduction;
  const renewablePercentage = renewableRatio !== null ? Math.round(100 * renewableRatio) : '?';

  return (
    <Tooltip id="country-tooltip" position={position} onClose={onClose}>
      <div className="zone-name-header">
        <ZoneName zone={zoneData.countryCode} />
      </div>
      <TooltipContent
        hasData={zoneData.hasData}
        isDataDelayed={isDataDelayed}
        co2intensity={co2intensity}
        fossilFuelPercentage={fossilFuelPercentage}
        renewablePercentage={renewablePercentage}
      />
    </Tooltip>
  );
};

export default connect(mapStateToProps)(MapCountryTooltip);
