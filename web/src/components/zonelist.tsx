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
// @ts-expect-error TS(7016): Could not find a declaration file for module 'd3-a... Remove this comment to see the full error message
import { ascending } from 'd3-array';
// @ts-expect-error TS(7016): Could not find a declaration file for module 'd3-c... Remove this comment to see the full error message
import { values } from 'd3-collection';
import { useTrackEvent } from '../hooks/tracking';
import { useCurrentZoneList } from '../hooks/redux';

function withZoneRankings(zones: any) {
  return zones.map((zone: any) => {
    const ret = Object.assign({}, zone);
    ret.ranking = zones.indexOf(zone) + 1;
    return ret;
  });
}

function getCo2IntensityAccessor(electricityMixMode: any) {
  return (d: any) => (electricityMixMode === 'consumption' ? d.co2intensity : d.co2intensityProduction);
}

function sortAndValidateZones(zones: any, accessor: any) {
  return zones.filter(accessor).sort((x: any, y: any) => {
    if (!x.co2intensity && !x.countryCode) {
      return ascending(x.countryCode, y.countryCode);
    }
    return ascending(accessor(x) ?? Infinity, accessor(y) ?? Infinity);
  });
}

function processZones(zonesData: any, accessor: any) {
  const zones = values(zonesData);
  const validatedAndSortedZones = sortAndValidateZones(zones, accessor);
  return withZoneRankings(validatedAndSortedZones);
}

function zoneMatchesQuery(zone: any, queryString: any) {
  if (!queryString) {
    return true;
  }
  const queries = queryString.split(' ');
  return queries.every(
    (query: any) => getZoneNameWithCountry(zone.countryCode).toLowerCase().indexOf(query.toLowerCase()) !== -1
  );
}

const mapStateToProps = (state: any) => ({
  electricityMixMode: state.application.electricityMixMode,
  searchQuery: state.application.searchQuery,
});

const Flag = styled.img`
  margin-right: 10px;
  margin-left: 10px;
  vertical-align: middle;
`;

const ZoneList = ({ electricityMixMode, searchQuery }: any) => {
  const zonesList = useCurrentZoneList();
  const co2ColorScale = useCo2ColorScale();
  const co2IntensityAccessor = getCo2IntensityAccessor(electricityMixMode);
  const zones = processZones(zonesList, co2IntensityAccessor).filter((z: any) => zoneMatchesQuery(z, searchQuery));

  const listRef = React.createRef();
  const history = useHistory();
  const location = useLocation();
  const trackEvent = useTrackEvent();
  const [selectedItemIndex, setSelectedItemIndex] = useState(null);

  const zonePage = (zone: any) => ({
    pathname: `/zone/${zone.countryCode}`,
    search: location.search,
  });

  const enterZone = (zone: any) => {
    dispatchApplication('mapViewport', getCenteredLocationViewport(zone.center));
    trackEvent('ZoneInRanking Clicked', { zone: zone.countryCode });
    history.push(zonePage(zone));
  };

  // Keyboard navigation
  useEffect(() => {
    const keyHandler = (e: any) => {
      if (e.key) {
        let nextItemIndex, prevItemIndex;
        switch (e.key) {
          case 'Enter':
            // @ts-expect-error TS(2538): Type 'null' cannot be used as an index type.
            zones[selectedItemIndex] && enterZone(zones[selectedItemIndex]);
            break;
          case 'ArrowUp':
            prevItemIndex = selectedItemIndex === null ? 0 : Math.max(0, selectedItemIndex - 1);
            (listRef as any).current?.scrollToItem(prevItemIndex);
            // @ts-expect-error TS(2345): Argument of type 'number' is not assignable to par... Remove this comment to see the full error message
            setSelectedItemIndex(prevItemIndex);
            break;
          case 'ArrowDown':
            nextItemIndex = selectedItemIndex === null ? 0 : Math.min(zones.length - 1, selectedItemIndex + 1);
            (listRef as any).current?.scrollToItem(nextItemIndex);
            // @ts-expect-error TS(2345): Argument of type 'number' is not assignable to par... Remove this comment to see the full error message
            setSelectedItemIndex(nextItemIndex);
            break;
          case e.key.match(/^[A-z]$/)?.input:
            // Focus on the first item if modified the search query
            (listRef as any).current?.scrollToItem(0, 'start');
            // @ts-expect-error TS(2345): Argument of type '0' is not assignable to paramete... Remove this comment to see the full error message
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
      // @ts-expect-error TS(2531): Object is possibly 'null'.
      setHeight(targetElement.clientHeight);
    });
    // @ts-expect-error TS(2345): Argument of type 'Element | null' is not assignabl... Remove this comment to see the full error message
    observer.observe(targetElement);
    return () => {
      // @ts-expect-error TS(2345): Argument of type 'Element | null' is not assignabl... Remove this comment to see the full error message
      observer.unobserve(targetElement);
    };
  }, []);

  /**
   * The HTML (JSX) for each row that should be rendered.
   */
  const Row = memo(({ index, style }: any) => {
    return (
      <Link
        style={style} // This one is important to keep the list from flickering when scrolling.
        to={zonePage(zones[index])}
        onClick={() => enterZone(zones[index])}
        className={selectedItemIndex === index ? 'selected' : undefined}
      >
        <div className="ranking">{zones[index].ranking}</div>
        <Flag src={flagUri(zones[index].countryCode, 32)} height={32} width={32} alt={zones[index].countryCode} />
        <div className="name">
          <div className="zone-name">{getZoneName(zones[index].countryCode)}</div>
          <div className="country-name">{getCountryName(zones[index].countryCode)}</div>{' '}
        </div>
        <div
          className="co2-intensity-tag"
          style={{ backgroundColor: co2ColorScale(co2IntensityAccessor(zones[index])) }}
        />
      </Link>
    );
  }, areEqual);

  return (
    <List
      className="zone-list"
      ref={listRef}
      height={height}
      itemSize={35}
      itemCount={zones.length}
      itemKey={(index: any) => {
        return zones[index].countryCode;
      }}
    >
      {Row}
    </List>
  );
};

export default connect(mapStateToProps)(ZoneList);
