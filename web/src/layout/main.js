/* eslint-disable react/jsx-no-target-blank */
/* eslint-disable jsx-a11y/anchor-is-valid */
// TODO(olc): re-enable this rule

import React from 'react';
import { connect, useSelector } from 'react-redux';
import { useLocation } from 'react-router-dom';

// Layout
import Header from './header';
import LayerButtons from './layerbuttons';
import LeftPanel from './leftpanel';
import Legend from './legend';
import Tabs from './tabs';
import MapTooltips from './maptooltips';

// Modules
import { __ } from '../helpers/translation';
import { isNewClientVersion } from '../helpers/environment';
import { useCustomDatetime } from '../helpers/router';
import { useLoadingOverlayVisible } from '../hooks/redux';
import {
  useClientVersionFetch,
  useGridDataPolling,
  useConditionalWindDataPolling,
  useConditionalSolarDataPolling,
} from '../hooks/fetch';
import { dispatch, dispatchApplication } from '../store';
import OnboardingModal from '../components/onboardingmodal';
import LoadingOverlay from '../components/loadingoverlay';
import Toggle from '../components/toggle';

import WindLayer from '../components/layers/windlayer';

// TODO: Move all styles from styles.css to here
// TODO: Remove all unecessary id and class tags

const mapStateToProps = state => ({
  brightModeEnabled: state.application.brightModeEnabled,
  electricityMixMode: state.application.electricityMixMode,
  hasConnectionWarning: state.data.hasConnectionWarning,
  isLeftPanelCollapsed: state.application.isLeftPanelCollapsed,
  version: state.application.version,
});

const Main = ({
  brightModeEnabled,
  electricityMixMode,
  isLeftPanelCollapsed,
  hasConnectionWarning,
  version,
}) => {
  const location = useLocation();
  const datetime = useCustomDatetime();

  const showLoadingOverlay = useLoadingOverlayVisible();

  // Check for the latest client version once initially.
  useClientVersionFetch();

  // Start grid data polling as soon as the app is mounted.
  useGridDataPolling();

  // Poll wind data if the toggle is enabled.
  useConditionalWindDataPolling();

  // Poll solar data if the toggle is enabled.
  useConditionalSolarDataPolling();

  return (
    <React.Fragment>
      <div
        style={{
          position: 'fixed', /* This is done in order to ensure that dragging will not affect the body */
          width: '100vw',
          height: 'inherit',
          display: 'flex',
          flexDirection: 'column', /* children will be stacked vertically */
          alignItems: 'stretch', /* force children to take 100% width */
        }}
      >
        <Header />
        <div id="inner">
          <LoadingOverlay visible={showLoadingOverlay} />
          <LeftPanel />
          <div id="map-container" className={location.pathname !== '/map' ? 'small-screen-hidden' : ''}>
            <div id="zones" className="map-layer" />
            <WindLayer />
            <canvas id="solar" className="map-layer" />
            <div id="watermark" className={`watermark small-screen-hidden ${brightModeEnabled ? 'brightmode' : ''}`}>
              <a href="http://www.tmrow.com/mission?utm_source=electricitymap.org&utm_medium=referral&utm_campaign=watermark" target="_blank">
                <div id="built-by-tomorrow" />
              </a>
              <a id="hiring-flag" href="https://tmrow.com/jobs" target="_blank">
                <p>we&apos;re hiring!</p>
              </a>
            </div>
            <Legend />
            <div className="controls-container">
              <Toggle
                infoHTML={__('tooltips.cpinfo')}
                onChange={value => dispatchApplication('electricityMixMode', value)}
                options={[
                  { value: 'production', label: __('tooltips.production') },
                  { value: 'consumption', label: __('tooltips.consumption') },
                ]}
                value={electricityMixMode}
              />
            </div>
            <LayerButtons />
          </div>

          <div id="connection-warning" className={`flash-message ${hasConnectionWarning ? 'active' : ''}`}>
            <div className="inner">
              {__('misc.oops')}
              {' '}
              <a
                href=""
                onClick={(e) => {
                  dispatch({ type: 'GRID_DATA_FETCH_REQUESTED', payload: { datetime } });
                  e.preventDefault();
                }}
              >
                {__('misc.retrynow')}
              </a>
              .
            </div>
          </div>
          <div id="new-version" className={`flash-message ${isNewClientVersion(version) ? 'active' : ''}`}>
            <div className="inner">
              {__('misc.newversion')}
            </div>
          </div>

          <div
            id="left-panel-collapse-button"
            className={`small-screen-hidden ${isLeftPanelCollapsed ? 'collapsed' : ''}`}
            onClick={() => dispatchApplication('isLeftPanelCollapsed', !isLeftPanelCollapsed)}
            role="button"
            tabIndex="0"
          >
            <i className="material-icons">arrow_drop_down</i>
          </div>

          { /* end #inner */}
        </div>
        <Tabs />
      </div>
      {/* TODO: Get rid of this as a part of https://github.com/tmrowco/electricitymap-contrib/issues/2288 */}
      <MapTooltips />
      <OnboardingModal />
    </React.Fragment>
  );
};

export default connect(mapStateToProps)(Main);
