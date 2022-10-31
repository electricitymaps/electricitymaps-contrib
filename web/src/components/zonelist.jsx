import React, { useState, useEffect, memo } from 'react';
import { Link, useLocation, useHistory } from 'react-router-dom';
import { FixedSizeList as List, areEqual } from 'react-window';
import { connect } from 'react-redux';
import styled from 'styled-components';

import { dispatchApplication } from '../store';
import { useCo2ColorScale } from '../hooks/theme';
import { getCenteredLocationViewport } from '../helpers/map';
import { getZoneNameWithCountry, getZoneName, getCountryName } from '../helpers/translation';
import { flagUri } from '../helpers/flags';
import { ascending } from 'd3-array';
import { values } from 'd3-collection';
import { useTrackEvent } from '../hooks/tracking';
import { useCurrentZoneList } from '../hooks/redux';

function withZoneRankings(zones) {
  return zones.map((zone) => {
    const ret = Object.assign({}, zone);
    ret.ranking = zones.indexOf(zone) + 1;
    return ret;
  });
}

function getCo2IntensityAccessor(electricityMixMode) {
  return (d) => (electricityMixMode === 'consumption' ? d.co2intensity : d.co2intensityProduction);
}

function sortAndValidateZones(zones, accessor) {
  return zones.filter(accessor).sort((x, y) => {
    if (!x.co2intensity && !x.countryCode) {
      return ascending(x.countryCode, y.countryCode);
    }
    return ascending(accessor(x) ?? Infinity, accessor(y) ?? Infinity);
  });
}

function processZones(zonesData, accessor) {
  const zones = values(zonesData);
  const validatedAndSortedZones = sortAndValidateZones(zones, accessor);
  return withZoneRankings(validatedAndSortedZones);
}

function zoneMatchesQuery(zone, queryString) {
  if (!queryString) {
    return true;
  }
  const queries = queryString.split(' ');
  return queries.every(
    (query) => getZoneNameWithCountry(zone.countryCode).toLowerCase().indexOf(query.toLowerCase()) !== -1
  );
}

const mapStateToProps = (state) => ({
  electricityMixMode: state.application.electricityMixMode,
  searchQuery: state.application.searchQuery,
});

const ZoneListContainer = styled(List)`
  overflow-y: scroll;
  flex: 1;
  -webkit-overflow-scrolling: touch;

  p {
    margin: 0;
    display: flex;
    flex-direction: column;
    width: 100%;
  }

  a {
    color: var(--black);
    display: flex;
    font-size: 1rem;
    justify-content: end;
    align-items: center;
    box-sizing: content-box;

    /* formatting */
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;
    line-height: 1rem;

    &:hover {
      text-decoration: none;
      background: rgb(235, 235, 235);
    }

    &.selected {
      background-color: rgb(235, 235, 235);
    }
  }
`;

const Flag = styled.img`
  margin-right: 10px;
  margin-left: 10px;
  vertical-align: middle;
`;

const CO2IntensityTag = styled.div`
  border-radius: 3px;
  margin-right: 10px;
  height: 17px;
  width: 17px;
`;

const Ranking = styled.div`
  width: 2rem;
  display: flex;
  justify-content: center;
  flex-direction: column;
  text-align: center;
`;

const RowName = styled.div`
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
  flex: 1;
`;

const CountryName = styled.div`
  font-size: 0.7rem;
`;

const ZoneName = styled.div`
  font-size: 0.9rem;
  margin-right: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

const ZoneList = ({ electricityMixMode, searchQuery }) => {
  const zonesList = useCurrentZoneList();
  const co2ColorScale = useCo2ColorScale();
  const co2IntensityAccessor = getCo2IntensityAccessor(electricityMixMode);
  const zones = processZones(zonesList, co2IntensityAccessor).filter((z) => zoneMatchesQuery(z, searchQuery));

  const listRef = React.createRef();
  const history = useHistory();
  const location = useLocation();
  const trackEvent = useTrackEvent();
  const [selectedItemIndex, setSelectedItemIndex] = useState(null);

  const zonePage = (zone) => ({
    pathname: `/zone/${zone.countryCode}`,
    search: location.search,
  });

  const enterZone = (zone) => {
    dispatchApplication('mapViewport', getCenteredLocationViewport(zone.center));
    trackEvent('ZoneInRanking Clicked', { zone: zone.countryCode });
    history.push(zonePage(zone));
  };

  // Keyboard navigation
  useEffect(() => {
    const keyHandler = (e) => {
      if (e.key) {
        let nextItemIndex, prevItemIndex;
        switch (e.key) {
          case 'Enter':
            zones[selectedItemIndex] && enterZone(zones[selectedItemIndex]);
            break;
          case 'ArrowUp':
            prevItemIndex = selectedItemIndex === null ? 0 : Math.max(0, selectedItemIndex - 1);
            listRef.current?.scrollToItem(prevItemIndex);
            setSelectedItemIndex(prevItemIndex);
            break;
          case 'ArrowDown':
            nextItemIndex = selectedItemIndex === null ? 0 : Math.min(zones.length - 1, selectedItemIndex + 1);
            listRef.current?.scrollToItem(nextItemIndex);
            setSelectedItemIndex(nextItemIndex);
            break;
          case e.key.match(/^[A-z]$/)?.input:
            // Focus on the first item if modified the search query
            listRef.current?.scrollToItem(0, 'start');
            setSelectedItemIndex(0);
            break;
        }
      }
    };
    document.addEventListener('keyup', keyHandler);
    return () => {
      document.removeEventListener('keyup', keyHandler);
    };
  });

  /**
   *  Used to pass numerical height to List component.
   */
  const [height, setHeight] = useState(0);

  /**
   * Listens for changes in the size of the zone-list and updates the height property when a change is detected.
   * Setting the hight this way ensures there are no more dom elements than necessary.
   */
  useEffect(() => {
    const targetElement = document.querySelector('.zone-list');
    const observer = new ResizeObserver(() => {
      setHeight(targetElement.clientHeight);
    });
    observer.observe(targetElement);
    return () => {
      observer.unobserve(targetElement);
    };
  }, []);

  /**
   * The HTML (JSX) for each row that should be rendered.
   */
  const Row = memo(({ index, style }) => {
    return (
      <Link
        style={style} // This one is important to keep the list from flickering when scrolling.
        to={zonePage(zones[index])}
        onClick={() => enterZone(zones[index])}
        className={selectedItemIndex === index ? 'selected' : undefined}
      >
        <Ranking>{zones[index].ranking}</Ranking>
        <Flag src={flagUri(zones[index].countryCode, 32)} height={32} width={32} alt={zones[index].countryCode} />
        <RowName>
          <ZoneName>{getZoneName(zones[index].countryCode)}</ZoneName>
          <CountryName>{getCountryName(zones[index].countryCode)}</CountryName>{' '}
        </RowName>
        <CO2IntensityTag style={{ backgroundColor: co2ColorScale(co2IntensityAccessor(zones[index])) }} />
      </Link>
    );
  }, areEqual);

  return (
    <ZoneListContainer
      className="zone-list"
      ref={listRef}
      height={height}
      itemSize={35}
      itemCount={zones.length}
      itemKey={(index) => {
        return zones[index].countryCode;
      }}
    >
      {Row}
    </ZoneListContainer>
  );
};

export default connect(mapStateToProps)(ZoneList);
