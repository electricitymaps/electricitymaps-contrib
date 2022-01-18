import React from 'react';
import { connect } from 'react-redux';
import { useParams } from 'react-router-dom';

import { __ } from '../helpers/translation';
import { useCurrentZoneData } from '../hooks/redux';

const getMessage = (zoneId, zoneData, zoneTimeIndex) => {
  const isRealtimeData = zoneTimeIndex === null;
  const isDataDelayed = zoneData.delays && zoneData.delays.production;

  let message = __('country-panel.noDataAtTimestamp');
  if (isRealtimeData) {
    const link = `https://storage.googleapis.com/electricitymap-parser-logs/${zoneId}.html`;
    message = `${__('country-panel.noLiveData')}. ${__('country-panel.helpUs', link)}`;
  }

  if (isDataDelayed) {
    message = __('country-panel.dataIsDelayed', zoneData.delays.production);
  }

  return message;
};

const mapStateToProps = (state) => ({
  zoneTimeIndex: state.application.selectedZoneTimeIndex,
});

const CountryTableOverlayIfNoData = ({ zoneTimeIndex }) => {
  const { zoneId } = useParams();
  const zoneData = useCurrentZoneData();

  // TODO: Shouldn't be hardcoded
  const zonesThatCanHaveZeroProduction = ['AX', 'DK-BHM', 'CA-PE', 'ES-IB-FO'];
  const zoneHasProductionValues = zoneData.production && !Object.values(zoneData.production).every(v => v === null);
  const zoneHasProductionData = zoneHasProductionValues || zonesThatCanHaveZeroProduction.includes(zoneId);
  // note that the key can be both null and undefined, so we need to check for both (so != instead of !==)
  const isEstimated = zoneData.estimationMethod != null; 


  const shouldHideOverlay = (zoneHasProductionData && zoneData.hasParser) || isEstimated;
  if (shouldHideOverlay) {
    return null;
  }

  const message = getMessage(zoneId, zoneData, zoneTimeIndex);

  return (
    <div className="no-data-overlay visible">
      <div className="no-data-overlay-background" />
      <div
        className="no-data-overlay-message"
        dangerouslySetInnerHTML={{
          __html: message,
        }}
      />
    </div>
  );
};

export default connect(mapStateToProps)(CountryTableOverlayIfNoData);
