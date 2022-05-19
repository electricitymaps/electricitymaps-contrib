import React from 'react';

import { useTranslation } from '../../helpers/translation';
import { dispatchApplication } from '../../store';

import SearchBar from '../../components/searchbar';
import ZoneList from '../../components/zonelist';

import InfoText from './infotext';
import { useFeatureToggle } from '../../hooks/router';
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
  margin-bottom: ${(props) => (props.historyFeatureEnabled ? '170px' : 0)};

  .info-text {
    flex-direction: column;
    padding: 1rem 1rem 0 1rem;
  }
`;

const ZoneListPanel = () => {
  const { __ } = useTranslation();
  const isHistoryFeatureEnabled = useFeatureToggle('history');

  return (
    <StyledWrapper historyFeatureEnabled={isHistoryFeatureEnabled}>
      <div className="zone-list-header">
        <div className="title"> {__('left-panel.zone-list-header-title')}</div>
        <div className="subtitle">{__('left-panel.zone-list-header-subtitle')}</div>
      </div>

      <SearchBar
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
