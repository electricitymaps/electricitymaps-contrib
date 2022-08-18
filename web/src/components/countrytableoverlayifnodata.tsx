import React from 'react';
import { connect } from 'react-redux';

import { useParams } from 'react-router-dom';

import { useTranslation } from '../helpers/translation';
import { useCurrentZoneData } from '../hooks/redux';

const getMessage = (__: any, zoneId: any, zoneData: any, zoneTimeIndex: any) => {
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

const mapStateToProps = (state: any) => ({
  zoneTimeIndex: state.application.selectedZoneTimeIndex,
});

const CountryTableOverlayIfNoData = ({ zoneTimeIndex }: any) => {
  const { zoneId } = useParams();
  const zoneData = useCurrentZoneData();
  const { __ } = useTranslation();

  if (zoneData.hasData) {
    return null;
  }

  const message = getMessage(__, zoneId, zoneData, zoneTimeIndex);

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
