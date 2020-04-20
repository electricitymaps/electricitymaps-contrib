import React from 'react';

import { __ } from '../../helpers/translation';
import { co2Sub } from '../../helpers/formatting';
import { dispatchApplication } from '../../store';

import SearchBar from '../../components/searchbar';
import ZoneList from '../../components/zonelist';

import InfoText from './infotext';

const documentSearchKeyUpHandler = (key, searchRef) => {
  if (key === '/') {
    // Reset input and focus
    if (searchRef.current) {
      searchRef.current.value = '';
      searchRef.current.focus();
    }
  } else if (key && key.match(/^[A-z]$/)) {
    // If input is not focused, focus it and append the pressed key
    if (searchRef.current && searchRef.current !== document.activeElement) {
      searchRef.current.value += key;
      searchRef.current.focus();
    }
  }
};

const ZoneListPanel = () => (
  <div className="left-panel-zone-list">
    <div className="zone-list-header">
      <div className="title">
        {' '}
        {__('left-panel.zone-list-header-title')}
      </div>
      <div
        className="subtitle"
        dangerouslySetInnerHTML={{
          __html: co2Sub(__('left-panel.zone-list-header-subtitle')),
        }}
      />
    </div>

    <SearchBar
      className="zone-search-bar"
      placeholder={__('left-panel.search')}
      documentKeyUpHandler={documentSearchKeyUpHandler}
      searchHandler={query => dispatchApplication('searchQuery', query)}
    />

    <ZoneList />

    <InfoText />
  </div>
);

export default ZoneListPanel;
