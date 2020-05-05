import React from 'react';
import { connect } from 'react-redux';

import { __, getFullZoneName } from '../../helpers/translation';
import { useCo2ColorScale } from '../../hooks/theme';
import { flagUri } from '../../helpers/flags';

import CircularGauge from '../circulargauge';
import Tooltip from '../tooltip';
import { ZoneName } from './common';

const mapStateToProps = state => ({
  electricityMixMode: state.application.electricityMixMode,
});

const MapCountryTooltip = ({
  electricityMixMode,
  position,
  zoneData,
}) => {
  const co2ColorScale = useCo2ColorScale();

  if (!zoneData) return null;

  const co2intensity = electricityMixMode === 'consumption'
    ? zoneData.co2intensity
    : zoneData.co2intensityProduction;

  const fossilFuelRatio = electricityMixMode === 'consumption'
    ? zoneData.fossilFuelRatio
    : zoneData.fossilFuelRatioProduction;
  const fossilFuelPercentage = fossilFuelRatio !== null
    ? Math.round(100 * (1 - fossilFuelRatio))
    : '?';

  const renewableRatio = electricityMixMode === 'consumption'
    ? zoneData.renewableRatio
    : zoneData.renewableRatioProduction;
  const renewablePercentage = renewableRatio !== null
    ? Math.round(100 * renewableRatio)
    : '?';

  return (
    <Tooltip id="country-tooltip" position={position}>
      <div className="zone-name-header">
        <ZoneName zone={zoneData.countryCode} />
      </div>
      {zoneData.hasParser ? (
        co2intensity ? (
          <div className="zone-details">
            <div className="country-table-header-inner">
              <div className="country-col country-emission-intensity-wrap">
                <div
                  id="country-emission-rect"
                  className="country-col-box emission-rect emission-rect-overview"
                  style={{ backgroundColor: co2ColorScale(co2intensity) }}
                >
                  <div>
                    <span className="country-emission-intensity">
                      {Math.round(co2intensity) || '?'}
                    </span>
                    g
                  </div>
                </div>
                <div className="country-col-headline">{__('country-panel.carbonintensity')}</div>
              </div>
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
            </div>
          </div>
        ) : (
          <div className="temporary-outage-text">
            {__('tooltips.temporaryDataOutage')}
          </div>
        )
      ) : (
        <div className="no-parser-text">
          <span dangerouslySetInnerHTML={{ __html: __('tooltips.noParserInfo', 'https://github.com/tmrowco/electricitymap-contrib#adding-a-new-region') }} />
        </div>
      )}
    </Tooltip>
  );
};

export default connect(mapStateToProps)(MapCountryTooltip);
