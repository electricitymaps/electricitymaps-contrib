import React from 'react';
import { connect } from 'react-redux';

import { __ } from '../helpers/translation';
import { getCurrentZoneData } from '../selectors';
import { useParams } from 'react-router-dom';

const mapStateToProps = state => ({
  zoneData: getCurrentZoneData(state),
  zoneTimeIndex: state.application.selectedZoneTimeIndex,
});

const CountryTableOverlayIfNoData = ({ zoneData, zoneTimeIndex }) => {
  const { zoneId } = useParams();

  const zonesThatCanHaveZeroProduction = ['AX', 'DK-BHM', 'CA-PE', 'ES-IB-FO'];
  const zoneHasNotProductionDataAtTimestamp = (!zoneData.production || !Object.keys(zoneData.production).length) && !zonesThatCanHaveZeroProduction.includes(zoneId);
  const zoneIsMissingParser = !zoneData.hasParser;
  const zoneHasData = zoneHasNotProductionDataAtTimestamp && !zoneIsMissingParser;
  const isRealtimeData = zoneTimeIndex === null;

  if (!zoneHasData) return null;

  return (
    <div className="no-data-overlay visible">
      <div className="overlay no-data-overlay-background" />
      <div className="no-data-overlay-message">
        {__(isRealtimeData ? 'country-panel.noLiveData' : 'country-panel.noDataAtTimestamp')}
      </div>
    </div>
  );
};

export default connect(mapStateToProps)(CountryTableOverlayIfNoData);
