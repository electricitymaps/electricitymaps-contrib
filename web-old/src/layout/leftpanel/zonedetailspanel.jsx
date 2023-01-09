import React from 'react';
import { connect } from 'react-redux';

import { useConditionalZoneHistoryFetch } from '../../hooks/fetch';

import CountryPanel from './countrypanel';

const mapStateToProps = (state) => ({
  selectedZoneTimeIndex: state.application.selectedZoneTimeIndex,
});

const ZoneDetailsPanel = () => {
  // TODO: deprecate this componentx
  // Fetch history for the current zone if it hasn't been fetched yet.
  useConditionalZoneHistoryFetch();

  return (
    <div className="left-panel-zone-details">
      <CountryPanel />
    </div>
  );
};

export default connect(mapStateToProps)(ZoneDetailsPanel);
