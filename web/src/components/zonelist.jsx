import React, { useState, useEffect } from 'react';
import { Link, useLocation, useHistory } from 'react-router-dom';
import { connect } from 'react-redux';
import styled from 'styled-components';

import { dispatchApplication } from '../store';
import { useCo2ColorScale } from '../hooks/theme';
import { getCenteredZoneViewport } from '../helpers/map';
import { getZoneNameWithCountry, getZoneName, getCountryName } from '../helpers/translation';
import { flagUri } from '../helpers/flags';
import { ascending } from 'd3-array';
import { values } from 'd3-collection';
import { useTrackEvent } from '../hooks/tracking';

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
      return ascending(x.shortname || x.countryCode, y.shortname || y.countryCode);
    }
    return ascending(accessor(x) || Infinity, accessor(y) || Infinity);
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
  gridZones: state.data.grid.zones,
  searchQuery: state.application.searchQuery,
});

const Flag = styled.img`
  margin-right: 10px;
  margin-left: 10px;
  vertical-align: middle;
`;

const ZoneList = ({ electricityMixMode, gridZones, searchQuery }) => {
  const co2ColorScale = useCo2ColorScale();
  const co2IntensityAccessor = getCo2IntensityAccessor(electricityMixMode);
  const zones = processZones(gridZones, co2IntensityAccessor).filter((z) => zoneMatchesQuery(z, searchQuery));

  const ref = React.createRef();
  const history = useHistory();
  const location = useLocation();
  const trackEvent = useTrackEvent();
  const [selectedItemIndex, setSelectedItemIndex] = useState(null);

  const zonePage = (zone) => ({
    pathname: `/zone/${zone.countryCode}`,
    search: location.search,
  });

  const enterZone = (zone) => {
    dispatchApplication('mapViewport', getCenteredZoneViewport(zone));
    trackEvent('ZoneInRanking Clicked', { zone: zone.countryCode });
    history.push(zonePage(zone));
  };

  // Keyboard navigation
  useEffect(() => {
    const scrollToItemIfNeeded = (index) => {
      const item = ref.current && ref.current.children[index];
      if (!item) {
        return;
      }

      const parent = item.parentNode;
      const parentComputedStyle = window.getComputedStyle(parent, null);
      const parentBorderTopWidth = parseInt(parentComputedStyle.getPropertyValue('border-top-width'), 10);
      const overTop = item.offsetTop - parent.offsetTop < parent.scrollTop;
      const overBottom =
        item.offsetTop - parent.offsetTop + item.clientHeight - parentBorderTopWidth >
        parent.scrollTop + parent.clientHeight;
      const alignWithTop = overTop && !overBottom;

      if (overTop || overBottom) {
        item.scrollIntoView(alignWithTop);
      }
    };
    const keyHandler = (e) => {
      if (e.key) {
        if (e.key === 'Enter' && zones[selectedItemIndex]) {
          enterZone(zones[selectedItemIndex]);
        } else if (e.key === 'ArrowUp') {
          const prevItemIndex = selectedItemIndex === null ? 0 : Math.max(0, selectedItemIndex - 1);
          scrollToItemIfNeeded(prevItemIndex);
          setSelectedItemIndex(prevItemIndex);
        } else if (e.key === 'ArrowDown') {
          const nextItemIndex = selectedItemIndex === null ? 0 : Math.min(zones.length - 1, selectedItemIndex + 1);
          scrollToItemIfNeeded(nextItemIndex);
          setSelectedItemIndex(nextItemIndex);
        } else if (e.key.match(/^[A-z]$/)) {
          // Focus on the first item if modified the search query
          scrollToItemIfNeeded(0);
          setSelectedItemIndex(0);
        }
      }
    };
    document.addEventListener('keyup', keyHandler);
    return () => {
      document.removeEventListener('keyup', keyHandler);
    };
  });

  return (
    <div className="zone-list" ref={ref}>
      {zones.map((zone, ind) => (
        <Link
          to={zonePage(zone)}
          onClick={() => enterZone(zone)}
          className={selectedItemIndex === ind ? 'selected' : ''}
          key={zone.shortname}
        >
          <div className="ranking">{zone.ranking}</div>
          <Flag src={flagUri(zone.countryCode, 32)} alt={zone.countryCode} />
          <div className="name">
            <div className="zone-name">{getZoneName(zone.countryCode)}</div>
            <div className="country-name">{getCountryName(zone.countryCode)}</div>
          </div>
          <div className="co2-intensity-tag" style={{ backgroundColor: co2ColorScale(co2IntensityAccessor(zone)) }} />
        </Link>
      ))}
    </div>
  );
};

export default connect(mapStateToProps)(ZoneList);
