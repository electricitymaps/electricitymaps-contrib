import React from 'react';
import { connect } from 'react-redux';
import { useParams } from 'react-router-dom';

import { __ } from '../helpers/translation';
import { useCurrentZoneData } from '../hooks/redux';

const mapStateToProps = state => ({
  zoneTimeIndex: state.application.selectedZoneTimeIndex,
});

const CountryTableOverlayIfNoData = ({ zoneTimeIndex }) => {
  const { zoneId } = useParams();
  const zoneData = useCurrentZoneData();

  // TODO: Shouldn't be hardcoded
  const zonesThatCanHaveZeroProduction = ['AX', 'DK-BHM', 'CA-PE', 'ES-IB-FO'];
  const zoneHasNotProductionDataAtTimestamp = (!zoneData.production || Object.values(zoneData.production).every(v => v === null)) && !zonesThatCanHaveZeroProduction.includes(zoneId);
  const zoneIsMissingParser = !zoneData.hasParser;
  const zoneHasData = zoneHasNotProductionDataAtTimestamp && !zoneIsMissingParser;
  const isRealtimeData = zoneTimeIndex === null;
  const isDataDelayed = zoneData.delays && zoneData.delays.production;

  if (!zoneHasData) return null;
  let message = isRealtimeData ? __('country-panel.noLiveData') : __('country-panel.noDataAtTimestamp');
  if (isDataDelayed) {
    message = __('country-panel.dataIsDelayed', zoneData.delays.production);
  }
  return (
    <div className="no-data-overlay visible">
      <div className="no-data-overlay-background" />
      <div className="no-data-overlay-message">
        {message}
        {(!isRealtimeData || isDataDelayed) ? null : (
          <React.Fragment>
            {'. '}
            {'Help us identify the problem by taking a look at the '}
            <a
              href="https://storage.googleapis.com/electricitymap-parser-logs/index.html"
              target="_blank"
              rel="noopener noreferrer"
            >
              runtime logs
            </a>
            , or contact our data provider.
          </React.Fragment>
        )}
      </div>
    </div>
  );
};

export default connect(mapStateToProps)(CountryTableOverlayIfNoData);
