/* eslint-disable jsx-a11y/click-events-have-key-events */
/* eslint-disable jsx-a11y/no-static-element-interactions */
import React from 'react';
import { connect } from 'react-redux';
import { scaleLinear } from 'd3-scale';

import { dispatchApplication } from '../store';
import { updateApplication } from '../actioncreators';
import { __ } from '../helpers/translation';

import HorizontalColorbar from '../components/horizontalcolorbar';
import { solarColor, windColor } from '../helpers/scales';
import { useSolarEnabled, useWindEnabled } from '../helpers/router';
import { useCo2ColorScale } from '../hooks/theme';

// TODO: Move styles from styles.css to here
// TODO: Remove all unecessary id and class tags

const mapStateToProps = state => ({
  co2ColorbarValue: state.application.co2ColorbarValue,
  legendVisible: state.application.legendVisible,
  solarColorbarValue: state.application.solarColorbarValue,
  windColorbarValue: state.application.windColorbarValue,
});

const Legend = ({
  co2ColorbarValue,
  legendVisible,
  solarColorbarValue,
  windColorbarValue,
}) => {
  const co2ColorScale = useCo2ColorScale();
  const solarEnabled = useSolarEnabled();
  const windEnabled = useWindEnabled();

  const mobileCollapsedClass = !legendVisible ? 'mobile-collapsed' : '';
  const toggleLegend = () => {
    dispatchApplication('legendVisible', !legendVisible);
  };

  return (
    <div className={`floating-legend-container ${mobileCollapsedClass}`}>
      <div className="floating-legend-mobile-header">
        <span>{__('misc.legend')}</span>
        <i className="material-icons toggle-legend-button" onClick={toggleLegend}>
          {legendVisible ? 'call_received' : 'call_made'}
        </i>
      </div>
      {legendVisible && (
        <React.Fragment>
          {windEnabled && (
            <div className={`wind-potential-legend floating-legend ${mobileCollapsedClass}`}>
              <div className="legend-header">
                {__('legends.windpotential')}<small> (m/s)</small>
              </div>
              <HorizontalColorbar
                id="wind-potential-bar"
                colorScale={windColor}
                currentValue={windColorbarValue}
                markerColor="black"
                ticksCount={6}
              />
            </div>
          )}
          {solarEnabled && (
            <div className={`solar-potential-legend floating-legend ${mobileCollapsedClass}`}>
              <div className="legend-header">
                {__('legends.solarpotential')}<small> (W/m<span className="sup">2</span>)</small>
              </div>
              <HorizontalColorbar
                id="solar-potential-bar"
                colorScale={solarColor}
                currentValue={solarColorbarValue}
                markerColor="red"
                ticksCount={5}
              />
            </div>
          )}
          <div className={`co2-legend floating-legend ${mobileCollapsedClass}`}>
            <div className="legend-header">
              {__('legends.carbonintensity')} <small>(gCO₂eq/kWh)</small>
            </div>
            <HorizontalColorbar
              id="carbon-intensity-bar"
              colorScale={co2ColorScale}
              currentValue={co2ColorbarValue}
              markerColor="white"
              ticksCount={5}
            />
          </div>
        </React.Fragment>
      )}
    </div>
  );
};

export default connect(mapStateToProps)(Legend);
