import React from 'react';
import { connect, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';

import { __ } from '../helpers/translation';
import { getZoneDataSelector } from '../selectors/redux';

const mapStateToProps = state => ({
  zoneTimeIndex: state.application.selectedZoneTimeIndex,
});

const CountryTableOverlayIfNoData = ({ zoneTimeIndex }) => {
  const { zoneId } = useParams();
  const zoneData = useSelector(getZoneDataSelector(zoneId));

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
