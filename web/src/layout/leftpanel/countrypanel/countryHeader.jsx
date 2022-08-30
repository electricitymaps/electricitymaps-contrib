import React from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import CountryDisclaimer from '../../../components/countrydisclaimer';
import Icon from '../../../components/icon';
import { flagUri } from '../../../helpers/flags';
import { getZoneNameWithCountry } from '../../../helpers/translation';
import { TimeDisplay } from '../../../components/timeDisplay';
import { LABEL_TYPES, ZoneLabel } from '../../../components/zonelabel';

const CountryNameTime = styled.div`
  font-size: smaller;
  margin-left: 25px;
`;

const CountryNameTimeTable = styled.div`
  display: flex;
  justify-content: space-between;
  margin-left: 1.2rem;
`;

const Flag = styled.img`
  vertical-align: bottom;
  padding-right: 0.8rem;
`;

const CountryTime = styled.div`
  white-space: nowrap;
  display: flex;
`;

const StyledTimeDisplay = styled(TimeDisplay)`
  margin-top: 0px;
`;

export const CountryHeader = ({ parentPage, zoneId, data, isMobile, isDataAggregated }) => {
  const { disclaimer, estimationMethod, stateDatetime, datetime } = data;
  const shownDatetime = stateDatetime || datetime;
  const isDataEstimated = !(estimationMethod == null);

  return (
    <div className="left-panel-zone-details-toolbar">
      <Link to={parentPage} className="left-panel-back-button">
        <Icon iconName="arrow_back" />
      </Link>
      <CountryNameTime>
        <CountryNameTimeTable>
          <div>
            <Flag id="country-flag" alt="" src={flagUri(zoneId, 24)} />
          </div>
          <div style={{ flexGrow: 1 }}>
            <div className="country-name">{getZoneNameWithCountry(zoneId)}</div>
            <CountryTime>
              {shownDatetime && <StyledTimeDisplay />}
              {isDataEstimated && <ZoneLabel type={LABEL_TYPES.ESTIMATED} isMobile={isMobile} />}
              {isDataAggregated && <ZoneLabel type={LABEL_TYPES.AGGREGATED} isMobile={isMobile} />}
            </CountryTime>
          </div>
          {disclaimer && <CountryDisclaimer text={disclaimer} isMobile={isMobile} />}
        </CountryNameTimeTable>
      </CountryNameTime>
    </div>
  );
};
