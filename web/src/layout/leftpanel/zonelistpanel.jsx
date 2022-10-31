import React from 'react';

import { useTranslation } from '../../helpers/translation';
import { dispatchApplication } from '../../store';

import SearchBar from '../../components/searchbar';
import ZoneList from '../../components/zonelist';

import InfoText from './infotext';
import styled from 'styled-components';

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

const StyledWrapper = styled.div`
  padding: 1rem;
  display: flex;
  flex-direction: column;
  flex: 1 1 0px;
  overflow-y: hidden;
  margin-bottom: 170px;

  .info-text {
    flex-direction: column;
    padding: 1rem 1rem 0 1rem;
  }
`;

const ZoneListHeader = styled.div`
  padding: 0 1rem 0.5rem 1rem;

  .subtitle {
    font-size: 0.8rem;
  }
`;

const ZoneSearchBar = styled(SearchBar)`
  padding: 0.75rem 0.5rem 1rem 1rem;

  input {
    height: 32px;
    background-color: $white;
    color: inherit;
    border: none;
    border-bottom: 1px solid lightgray;
    font-weight: 400;
    font-size: 1rem;
    width: 100%;
    padding: 0.2rem;
    font-family: inherit;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
  }
`;

const ZoneListPanel = () => {
  const { __ } = useTranslation();

  return (
    <StyledWrapper>
      <ZoneListHeader>
        <div className="title"> {__('left-panel.zone-list-header-title')}</div>
        <div className="subtitle">{__('left-panel.zone-list-header-subtitle')}</div>
      </ZoneListHeader>

      <ZoneSearchBar
        className="zone-search-bar"
        placeholder={__('left-panel.search')}
        documentKeyUpHandler={documentSearchKeyUpHandler}
        searchHandler={(query) => dispatchApplication('searchQuery', query)}
      />

      <ZoneList />

      <InfoText />
    </StyledWrapper>
  );
};

export default ZoneListPanel;
