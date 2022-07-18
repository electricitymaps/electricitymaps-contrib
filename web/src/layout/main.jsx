import React, { useState } from 'react';
import styled from 'styled-components';
import { connect, useDispatch, useSelector } from 'react-redux';
import { useLocation } from 'react-router-dom';
import { BottomSheet } from 'react-spring-bottom-sheet';

// Layout
import Header from './header';
import LayerButtons from './layerbuttons';
import LeftPanel from './leftpanel';
import Legend from './legend';
import Map from './map';
import TimeController from './timeController';
import TimeSliderHeader from '../components/timesliderheader';

// Modules
import { useTranslation } from '../helpers/translation';
import { isNewClientVersion } from '../helpers/environment';
import { useHeaderVisible } from '../hooks/router';
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
import { GRID_DATA_FETCH_REQUESTED } from '../helpers/redux';
import MobileLayerButtons from '../components/mobilelayerbuttons';
import HistoricalViewIntroModal from '../components/historicalviewintromodal';

const CLIENT_VERSION_CHECK_INTERVAL = 15 * 60 * 1000; // 15 minutes

// TODO: Move all styles from styles.css to here
// TODO: Remove all unecessary id and class tags

const mapStateToProps = (state) => ({
  brightModeEnabled: state.application.brightModeEnabled,
  electricityMixMode: state.application.electricityMixMode,
  hasConnectionWarning: state.data.hasConnectionWarning,
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

const StyledBottomSheet = styled(BottomSheet)`
  [data-rsbs-overlay] {
    z-index: ${(props) => (props.behind ? 0 : 5)};
  }
  [data-rsbs-scroll] {
    // Disables scrolling, as we want users to open the sheet instead of scrolling inside it
    overflow: hidden;
  }
`;

const fetcher = (...args) => fetch(...args).then((res) => res.json());

const Main = ({ electricityMixMode, hasConnectionWarning }) => {
  const { __ } = useTranslation();
  const dispatch = useDispatch();
  const location = useLocation();
  const headerVisible = useHeaderVisible();
  const clientType = useSelector((state) => state.application.clientType);
  const isLocalhost = useSelector((state) => state.application.isLocalhost);
  const [isClientVersionForceHidden, setIsClientVersionForceHidden] = useState(false);
  const isMobile = useSelector((state) => state.application.isMobile);

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
                  tooltipStyle={{ left: 4, width: 204, top: 49 }}
                />
              </HiddenOnMobile>
              <LayerButtons />
            </MapContainer>
            {/* // TODO: Get CountryPanel shown here in a separate BottomSheet behind the other one */}
            {isMobile ? (
              <StyledBottomSheet
                scrollLocking={false} // Ensures scrolling is not blocked on IOS
                open
                snapPoints={() => [60, 160]}
                blocking={false}
                header={<TimeSliderHeader />}
              >
                <TimeController />
              </StyledBottomSheet>
            ) : (
              <TimeController />
            )}
          </ErrorBoundary>

          <div id="connection-warning" className={`flash-message ${hasConnectionWarning ? 'active' : ''}`}>
            <div className="inner">
              {__('misc.oops')}{' '}
              <button
                type="button"
                onClick={(e) => {
                  dispatch(GRID_DATA_FETCH_REQUESTED());
                  e.preventDefault();
                }}
              >
                {__('misc.retrynow')}
              </button>
              .
            </div>
          </div>
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
