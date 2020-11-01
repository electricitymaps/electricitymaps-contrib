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
  const zoneHasNotProductionDataAtTimestamp = (!zoneData.production || !Object.keys(zoneData.production).length) && !zonesThatCanHaveZeroProduction.includes(zoneId);
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
              href={`https://kibana.electricitymap.org/app/kibana#/discover/10af54f0-0c4a-11e9-85c1-1d63df8c862c?_g=(refreshInterval:('$$hashKey':'object:232',display:'5%20minutes',pause:!f,section:2,value:300000),time:(from:now-24h,mode:quick,to:now))&_a=(columns:!(message,extra.key,level),filters:!(('$state':(store:appState),meta:(alias:!n,disabled:!t,index:'96f67170-0c49-11e9-85c1-1d63df8c862c',key:level,negate:!f,params:(query:ERROR,type:phrase),type:phrase,value:ERROR),query:(match:(level:(query:ERROR,type:phrase)))),('$state':(store:appState),meta:(alias:!n,disabled:!f,index:'96f67170-0c49-11e9-85c1-1d63df8c862c',key:extra.key,negate:!f,params:(query:${zoneId},type:phrase),type:phrase,value:${zoneId}),query:(match:(extra.key:(query:${zoneId},type:phrase))))),index:'96f67170-0c49-11e9-85c1-1d63df8c862c',interval:auto,query:(language:lucene,query:''),sort:!('@timestamp',desc))`}
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
