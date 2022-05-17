import React from 'react';
import styled from 'styled-components';
import { useTranslation } from '../../helpers/translation';

const StyledWrapper = styled.div`
  margin-top: 12px;
  .detail-bottom-section & {
    padding: 0 1.5rem;
    margin-bottom: 12px;
    margin-top: 0px;
  }
  @media (min-width: 768px) {
    display: ${({ hideOnDesktop }) => (hideOnDesktop ? 'none !important' : 'block')};
  }
  @media (max-width: 768px) {
    display: ${({ hideOnMobile }) => (hideOnMobile ? 'none !important' : 'block')};
  }
`;

const SocialButtons = ({ hideOnMobile, hideOnDesktop }) => {
  const { i18n } = useTranslation();
  if (hideOnMobile && hideOnDesktop) {
    return null;
  }

  return (
    <StyledWrapper hideOnDesktop={hideOnDesktop} hideOnMobile={hideOnMobile}>
      <div>
        {/* Facebook share */}
        <div className="fb-share-button" data-href="https://app.electricitymap.org/" data-layout="button_count" />
        {/* Twitter share */}
        <a
          className="twitter-share-button"
          data-url="https://app.electricitymap.org"
          data-via="electricitymap"
          data-lang={i18n.language}
        >
          &nbsp;
        </a>
        {/* Slack */}
        <span className="slack-button">
          <a href="https://slack.tmrow.com" target="_blank" className="slack-btn" rel="noreferrer">
            <span className="slack-ico" />
            <span className="slack-text">Slack</span>
          </a>
        </span>
      </div>
    </StyledWrapper>
  );
};

export default SocialButtons;
