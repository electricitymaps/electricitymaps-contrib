import React from 'react';
import { connect } from 'react-redux';

import { MAP_COUNTRY_TOOLTIP_KEY } from '../../helpers/constants';
import { __, getFullZoneName } from '../../helpers/translation';
import { getCo2Scale } from '../../helpers/scales';
import { co2Sub } from '../../helpers/formatting';
import { flagUri } from '../../helpers/flags';
import { dispatch } from '../../store';

import CircularGauge from '../circulargauge';
import Tooltip from '../tooltip';

const mapStateToProps = state => ({
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
  countryData: state.application.tooltipZoneData,
  electricityMixMode: state.application.electricityMixMode,
  visible: state.application.tooltipDisplayMode === MAP_COUNTRY_TOOLTIP_KEY,
});

const MapCountryTooltip = ({
  colorBlindModeEnabled,
  countryData,
  electricityMixMode,
  visible,
}) => {
  if (!countryData || !visible) return null;

  const co2ColorScale = getCo2Scale(colorBlindModeEnabled);

  const co2intensity = electricityMixMode === 'consumption'
    ? countryData.co2intensity
    : countryData.co2intensityProduction;
  if (co2intensity) {
    dispatch({ type: 'SET_CO2_COLORBAR_MARKER', payload: { marker: co2intensity } });
  }

  const fossilFuelRatio = electricityMixMode === 'consumption'
    ? countryData.fossilFuelRatio
    : countryData.fossilFuelRatioProduction;
  const fossilFuelPercentage = fossilFuelRatio !== null
    ? Math.round(100 * (1 - fossilFuelRatio))
    : '?';

  const renewableRatio = electricityMixMode === 'consumption'
    ? countryData.renewableRatio
    : countryData.renewableRatioProduction;
  const renewablePercentage = renewableRatio !== null
    ? Math.round(100 * renewableRatio)
    : '?';

  return (
    <Tooltip id="country-tooltip">
      <div className="zone-name-header">
        <img id="country-flag" className="flag" src={flagUri(countryData.countryCode)} />
        {' '}
        <b><span id="country-name">{getFullZoneName(countryData.countryCode)}</span></b>
      </div>
      {countryData.hasParser ? (
        co2intensity ? (
          <div className="zone-details">
            <div className="country-table-header-inner">
              <div className="country-col country-emission-intensity-wrap">
                <div
                  id="country-emission-rect"
                  className="country-col-box emission-rect emission-rect-overview"
                  style={{ backgroundColor: co2intensity ? co2ColorScale(co2intensity) : 'gray' }}
                >
                  <div>
                    <span className="country-emission-intensity">
                      {Math.round(co2intensity) || '?'}
                    </span>
                    g
                  </div>
                </div>
                <div
                  className="country-col-headline"
                  dangerouslySetInnerHTML={{ __html: co2Sub(__('country-panel.carbonintensity')) }}
                />
              </div>
              <div className="country-col country-lowcarbon-wrap">
                <div id="tooltip-country-lowcarbon-gauge" className="country-gauge-wrap">
                  <CircularGauge percentage={fossilFuelPercentage} />
                </div>
                <div
                  className="country-col-headline"
                  dangerouslySetInnerHTML={{ __html: co2Sub(__('country-panel.lowcarbon')) }}
                />
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
