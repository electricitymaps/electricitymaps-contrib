import React from 'react';
import styled from 'styled-components';
import Icon from '../../components/icon';

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
  if (hideOnMobile && hideOnDesktop) {
    return null;
  }

  return (
    <StyledWrapper hideOnDesktop={hideOnDesktop} hideOnMobile={hideOnMobile}>
      <div>
        {/* Facebook share */}
        <div className="fb-share-button" data-href="https://app.electricitymaps.com/" data-layout="button_count" />
        <a
          className="twitter-share-button"
          href="https://twitter.com/intent/tweet?url=https://www.app.electricitymaps.com"
          target="_blank"
          rel="noreferrer"
        >
          <Icon iconName={'twitter'} size={16} /> Tweet
        </a>
        {/* Slack */}
        <span className="slack-button">
          <a href="https://slack.electricitymaps.com" target="_blank" className="slack-btn" rel="noreferrer">
            <span className="slack-ico" />
            <span className="slack-text">Slack</span>
          </a>
        </span>
      </div>
    </StyledWrapper>
  );
};

export default SocialButtons;
