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
    display: ${({
      // @ts-expect-error TS(2339): Property 'hideOnDesktop' does not exist on type 'P... Remove this comment to see the full error message
      hideOnDesktop,
    }) => (hideOnDesktop ? 'none !important' : 'block')};
  }
  @media (max-width: 768px) {
    display: ${({
      // @ts-expect-error TS(2339): Property 'hideOnMobile' does not exist on type 'Pi... Remove this comment to see the full error message
      hideOnMobile,
    }) => (hideOnMobile ? 'none !important' : 'block')};
  }
`;

const SocialButtons = ({ hideOnMobile, hideOnDesktop }: any) => {
  if (hideOnMobile && hideOnDesktop) {
    return null;
  }

  return (
    // @ts-expect-error TS(2769): No overload matches this call.
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
          {/* @ts-expect-error TS(2322): Type '{ iconName: string; size: number; }' is not ... Remove this comment to see the full error message */}
          <Icon iconName={'twitter'} size={16} /> Tweet
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
