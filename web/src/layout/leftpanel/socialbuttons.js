import React from 'react';
import styled from 'styled-components';

const StyledWrapper = styled.div`
  @media (min-width: 768px) {
    display: ${({ hideOnDesktop }) => (hideOnDesktop ? 'none !important' : 'block')};
  }
  @media (max-width: 768px) {
    display: ${({ hideOnMobile }) => (hideOnMobile ? 'none !important' : 'block')};
  }
`;

const SocialButtons = ({ hideOnMobile, hideOnDesktop }) => {
  if (hideOnMobile && hideOnDesktop) {
    return null;
  }

  return (
    <StyledWrapper
      className="social-buttons"
      hideOnDesktop={hideOnDesktop}
      hideOnMobile={hideOnMobile}
    >
      <div>
        {/* Facebook share */}
        <div
          className="fb-share-button"
          data-href="https://app.electricitymap.org/"
          data-layout="button_count"
        />
        {/* Twitter share */}
        <a
          className="twitter-share-button"
          data-url="https://app.electricitymap.org"
          data-via="electricitymap"
          data-lang={locale}
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
