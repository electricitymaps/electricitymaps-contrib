import React, { useState } from 'react';
import styled from 'styled-components';
import { connect, useSelector } from 'react-redux';
import { useLocation, useHistory } from 'react-router-dom';

// Layout
import Header from './header';
import LayerButtons from './layerbuttons';
import LeftPanel from './leftpanel';
import Legend from './legend';
import Map from './map';
import TimeController from './timeController';

// Modules
import { useTranslation } from '../helpers/translation';
import { isNewClientVersion } from '../helpers/environment';
import { useHeaderVisible, useAggregatesToggle, useAggregatesEnabled } from '../hooks/router';
import { useLoadingOverlayVisible } from '../hooks/redux';
import { useGridDataPolling, useConditionalWindDataPolling, useConditionalSolarDataPolling } from '../hooks/fetch';
import { dispatchApplication } from '../store';
import OnboardingModal from '../components/onboardingmodal';
import InfoModal from '../components/infomodal';
import FAQModal from '../components/faqmodal';
import SettingsModal from '../components/settingsmodal';
import LoadingOverlay from '../components/loadingoverlay';
import Toggle from '../components/toggle';
import useSWR from 'swr';
import ErrorBoundary from '../components/errorboundary';
import MobileLayerButtons from '../components/mobilelayerbuttons';
import HistoricalViewIntroModal from '../components/historicalviewintromodal';
import ResponsiveSheet from './responsiveSheet';
import { RetryBanner } from '../components/retrybanner';
import { isAggregatedViewFF } from '../helpers/featureFlags';

const CLIENT_VERSION_CHECK_INTERVAL = 15 * 60 * 1000; // 15 minutes

// TODO: Move all styles from styles.css to here
// TODO: Remove all unecessary id and class tags

const mapStateToProps = (state) => ({
  brightModeEnabled: state.application.brightModeEnabled,
  electricityMixMode: state.application.electricityMixMode,
});

const MapContainer = styled.div`
  @media (max-width: 767px) {
    display: ${(props) => (props.pathname !== '/map' ? 'none !important' : 'block')};
  }
`;

const NewVersionInner = styled.div`
  background-color: #3f51b5;
`;

const NewVersionButton = styled.button`
  background: transparent;
  color: white;
  margin-left: 12px;
  background-color: inherit;
  border: none;
  cursor: pointer;
`;

const HiddenOnMobile = styled.div`
  @media (max-width: 767px) {
    display: none;
  }
`;

const fetcher = (...args) => fetch(...args).then((res) => res.json());

const Main = ({ electricityMixMode }) => {
  const { __ } = useTranslation();
  const location = useLocation();
  const history = useHistory();
  const headerVisible = useHeaderVisible();
  const clientType = useSelector((state) => state.application.clientType);
  const isLocalhost = useSelector((state) => state.application.isLocalhost);
  const [isClientVersionForceHidden, setIsClientVersionForceHidden] = useState(false);
  const isMobile = useSelector((state) => state.application.isMobile);
  const failedRequestType = useSelector((state) => state.data.failedRequestType);
  const showLoadingOverlay = useLoadingOverlayVisible();

  // Start grid data polling as soon as the app is mounted.
  useGridDataPolling();

  // Poll wind data if the toggle is enabled.
  useConditionalWindDataPolling();

  // Poll solar data if the toggle is enabled.
  useConditionalSolarDataPolling();

  const { data: clientVersionData } = useSWR('/client-version.json', fetcher, {
    refreshInterval: CLIENT_VERSION_CHECK_INTERVAL,
  });
  const clientVersion = clientVersionData && clientVersionData.version;

  let isClientVersionOutdated = false;
  // We only check the latest client version if running in browser on non-localhost.
  if (clientVersion && clientType === 'web' && !isLocalhost) {
    isClientVersionOutdated = isNewClientVersion(clientVersion);
  }

  if (isClientVersionOutdated) {
    console.warn(`Current client version: ${clientVersion} is outdated`);
  }

  const isAggregatedFFEnabled = isAggregatedViewFF();

  const toggleAggregates = useAggregatesToggle();

  const isAggregated = useAggregatesEnabled() ? 'aggregated' : 'detailed';

  return (
    <React.Fragment>
      <div
        style={{
          position: 'fixed' /* This is done in order to ensure that dragging will not affect the body */,
          width: '100vw',
          height: 'inherit',
          display: 'flex',
          flexDirection: 'column' /* children will be stacked vertically */,
          alignItems: 'stretch' /* force children to take 100% width */,
        }}
      >
        {headerVisible && <Header />}
        <div id="inner">
          <ErrorBoundary>
            <LoadingOverlay visible={showLoadingOverlay} />
            <LeftPanel />
            <MapContainer pathname={location.pathname} id="map-container">
              <Map />
              <MobileLayerButtons />
              <Legend />
              <HiddenOnMobile className="controls-container">
                <Toggle
                  infoHTML={__('tooltips.cpinfo')}
                  onChange={(value) => dispatchApplication('electricityMixMode', value)}
                  options={[
                    { value: 'production', label: __('tooltips.production') },
                    { value: 'consumption', label: __('tooltips.consumption') },
                  ]}
                  value={electricityMixMode}
                  tooltipStyle={{ left: 4, width: 204, top: 49, zindex: 520 }}
                />
                {isAggregatedFFEnabled && (
                  <Toggle
                    infoHTML={__('tooltips.aggregateinfo')}
                    onChange={() => history.push(toggleAggregates)}
                    options={[
                      { value: 'aggregated', label: __('tooltips.aggregated') },
                      { value: 'detailed', label: __('tooltips.detailed') },
                    ]}
                    value={isAggregated}
                    tooltipStyle={{ left: 4, width: 204, top: 79 }}
                  />
                )}
              </HiddenOnMobile>
              <LayerButtons />
            </MapContainer>
            {/* // TODO: Get CountryPanel shown here in a separate BottomSheet behind the other one */}
            {isMobile ? (
              <ResponsiveSheet visible={!showLoadingOverlay}>
                <TimeController />
              </ResponsiveSheet>
            ) : (
              <TimeController />
            )}
          </ErrorBoundary>
          {failedRequestType === 'grid' && <RetryBanner failedRequestType={failedRequestType} />}
          <div
            id="new-version"
            className={`flash-message ${isClientVersionOutdated && !isClientVersionForceHidden ? 'active' : ''}`}
          >
            <NewVersionInner className="inner">
              <span dangerouslySetInnerHTML={{ __html: __('misc.newversion') }} />
              <NewVersionButton onClick={() => setIsClientVersionForceHidden(true)}>&#x2715;</NewVersionButton>
            </NewVersionInner>
          </div>

          {/* end #inner */}
        </div>
      </div>
      <HistoricalViewIntroModal />
      <OnboardingModal />
      <InfoModal />
      <FAQModal />
      <SettingsModal />
    </React.Fragment>
  );
};

export default connect(mapStateToProps)(Main);
