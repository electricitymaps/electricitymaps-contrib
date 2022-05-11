import React, { useState } from 'react';
import styled from 'styled-components';
import SourceLabel from './CountrySourceLabel';
import { useTranslation } from '../helpers/translation';
import ContributorList from './contributorlist';
import Icon from './icon';

const EstimatedDataInfoBox = styled.p`
  font-size: 0.75rem;
  margin: 0;
`;

const InfoBox = styled.div`
  font-size: 0.75rem;
  margin-left: 0.5rem;
`;

const FlexDiv = styled.div`
  display: flex;
`;

const InlineFlexSpan = styled.span`
  display: inline-flex;
  align-items: center;
`;

const InfoFooter = ({ isMobile, isDataEstimated, data }) => {
  const { __ } = useTranslation();
  const [infoVisible, setInfoVisible] = useState({});

  const EstimatedDataInfo = ({ text }) => (
    <React.Fragment>
      <EstimatedDataInfoBox
        dangerouslySetInnerHTML={{
          __html: text,
        }}
      />
    </React.Fragment>
  );

  return (
    <>
      <FlexDiv>
        <InlineFlexSpan>
          Data type: <SourceLabel isMobile={isMobile} isDataEstimated={isDataEstimated} />
        </InlineFlexSpan>
        <InlineFlexSpan
          onClick={() => (infoVisible ? setInfoVisible(false) : setInfoVisible(true))}
          style={{ marginLeft: 'auto' }}
        >
          {infoVisible ? 'Collapse:' : 'Expand:'}
          <Icon iconName={infoVisible ? 'expand_less' : 'expand_more'} />
        </InlineFlexSpan>
      </FlexDiv>
      {infoVisible && (
        <InfoBox>
          <EstimatedDataInfo
            text={
              isDataEstimated ? __('country-panel.dataIsEstimated') : 'This data comes from a API.'
            }
          />
          {__('country-panel.source')}
          {': '}
          <a
            href="https://github.com/tmrowco/electricitymap-contrib/blob/master/DATA_SOURCES.md#real-time-electricity-data-sources"
            target="_blank"
          >
            <span className="country-data-source">{data.source || '?'}</span>
          </a>
        </InfoBox>
      )}

      <br />
      <FlexDiv>
        {'Contributors for this zone: '}
        <small style={{ marginLeft: 'auto' }}>
          <span
            dangerouslySetInnerHTML={{
              __html: __(
                'country-panel.addeditsource',
                'https://github.com/tmrowco/electricitymap-contrib/tree/master/parsers'
              ),
            }}
          />
        </small>
      </FlexDiv>
      <ContributorList />
    </>
  );
};

export default InfoFooter;
