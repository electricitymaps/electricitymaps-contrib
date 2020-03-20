/* eslint-disable jsx-a11y/click-events-have-key-events */
/* eslint-disable jsx-a11y/no-static-element-interactions */
import React from 'react';
import { connect } from 'react-redux';
import { scaleLinear } from 'd3-scale';

// Modules
import { updateApplication } from '../actioncreators';
import { __ } from '../helpers/translation';

import HorizontalColorbar from '../components/horizontalcolorbarreact';
import { getCo2Scale, maxSolarDSWRF } from '../helpers/scales';
import { co2Sub } from '../helpers/formatting';

// TODO: Move styles from styles.css to here
// TODO: Remove all unecessary id and class tags

const solarColorbarColor = scaleLinear()
  .domain([0, 0.5 * maxSolarDSWRF, maxSolarDSWRF])
  .range(['black', 'white', 'gold']);

const mapStateToProps = state => ({
  co2ColorbarMarker: state.application.co2ColorbarMarker,
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
  legendVisible: state.application.legendVisible,
  solarColorbarMarker: state.application.solarColorbarMarker,
  solarEnabled: state.application.solarEnabled,
});
const mapDispatchToProps = dispatch => ({
  dispatchApplication: (k, v) => dispatch(updateApplication(k, v)),
});

class Component extends React.PureComponent {
  toggleLegend = () => {
    this.props.dispatchApplication('legendVisible', !this.props.legendVisible);
  }

  render() {
    const {
      co2ColorbarMarker,
      colorBlindModeEnabled,
      legendVisible,
      solarColorbarMarker,
      solarEnabled,
    } = this.props;
    const mobileCollapsedClass = !legendVisible ? 'mobile-collapsed' : '';

    return (
      <div className={`floating-legend-container ${mobileCollapsedClass}`}>
        <div className="floating-legend-mobile-header">
          <span>{__('misc.legend')}</span>
          <i className={`material-icons toggle-legend-button up ${!legendVisible ? 'visible' : ''}`} onClick={this.toggleLegend}>call_made</i>
          <i className={`material-icons toggle-legend-button down ${legendVisible ? 'visible' : ''}`} onClick={this.toggleLegend}>call_received</i>
        </div>
        <div className={`wind-potential-legend floating-legend ${mobileCollapsedClass}`}>
          <div className="legend-header">
            {__('legends.windpotential')}
            {' '}
            <small>(m/s)</small>
          </div>
          <svg className="wind-potential-bar potential-bar colorbar" />
        </div>
        {solarEnabled && (
          <div className={`solar-potential-legend floating-legend ${mobileCollapsedClass}`}>
            <div className="legend-header">
              {__('legends.solarpotential')}<small> (W/m<span className="sup">2</span>)</small>
            </div>
            <HorizontalColorbar
              id="solar-potential-bar"
              colorScale={solarColorbarColor}
              currentMarker={co2ColorbarMarker}
              markerColor="red"
            />
          </div>
        )}
        <div className={`co2-legend floating-legend ${mobileCollapsedClass}`}>
          <div className="legend-header">
            <span dangerouslySetInnerHTML={{ __html: co2Sub(__('legends.carbonintensity')) }} />
            <small> (gCO<span className="sub">2</span>eq/kWh)</small>
          </div>
          <HorizontalColorbar
            id="carbon-intensity-bar"
            colorScale={getCo2Scale(colorBlindModeEnabled)}
            currentMarker={co2ColorbarMarker}
            markerColor="white"
          />
        </div>
      </div>
    );
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(Component);
