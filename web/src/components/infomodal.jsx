import React from 'react';
import { useTranslation } from '../helpers/translation';
import { dispatchApplication } from '../store';
import { useTrackEvent } from '../hooks/tracking';

import styled from 'styled-components';
import { useSelector } from 'react-redux';
import Modal from './modal';
import { Button } from './button';

const TermsAndPrivacyContainer = styled.div`
  padding: 1rem 0 0;
  text-align: center;
  a {
    margin-right: 1rem;
  }
`;

const InfoContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  p {
    margin-top: 0;
  }
`;

const FeedbackButton = styled(Button)`
  background-color: #44ab60;
  color: #fff;
`;
const GitHubButton = styled(Button)`
  background: linear-gradient(to right, #04275c 0%, #040e23 100%);
  color: #fff;
`;
const TwitterButton = styled(Button)`
  background-color: #1d9bf0;
  color: #fff;
`;
const SlackButton = styled(Button)`
  background-color: #4a154b;
  color: #fff;
`;

const InfoView = () => {
  const { __ } = useTranslation();
  const openFAQModal = () => dispatchApplication('faqModalOpen', true);

  return (
    <InfoContainer>
      <p>{__('info-modal.intro-text')}</p>
      <p
        dangerouslySetInnerHTML={{
          __html: __(
            'info-modal.open-source-text',
            'https://github.com/tmrowco/electricitymap-contrib',
            'https://github.com/tmrowco/electricitymap-contrib#data-sources'
          ),
        }}
      />
      <div>
        <Button onClick={openFAQModal} icon="info">
          FAQ
        </Button>
        <FeedbackButton href="https://forms.gle/VHaeHzXyGodFKZY18" icon="comment">
          {__('info-modal.feedback-button')}
        </FeedbackButton>
        <GitHubButton href="https://github.com/electricityMaps/electricitymaps-contrib" icon="github">
          {__('info-modal.github-button')}
        </GitHubButton>
        <TwitterButton href="https://twitter.com/intent/tweet?url=https://www.app.electricitymaps.com" icon="twitter">
          {__('info-modal.twitter-button')}
        </TwitterButton>
        <SlackButton href="https://slack.electricitymaps.com/" icon="slack">
          {__('info-modal.slack-button')}
        </SlackButton>
      </div>
      <TermsAndPrivacyContainer>
        <a href="https://www.electricitymaps.com/privacy-policy/">{__('info-modal.privacy-policy')}</a>
        <a href="https://www.electricitymaps.com/legal-notice/">{__('info-modal.legal-notice')}</a>
      </TermsAndPrivacyContainer>
    </InfoContainer>
  );
};

const views = [
  {
    title: (__) => __('info-modal.title'),
    renderContent: () => <InfoView />,
  },
];

const InfoModal = () => {
  const modalOpen = useSelector((state) => state.application.infoModalOpen);
  const trackEvent = useTrackEvent();

  const handleDismiss = () => {
    dispatchApplication('infoModalOpen', false);
  };

  const handleShown = () => {
    trackEvent('Info Modal Shown');
  };

  return (
    <Modal modalName={'info'} visible={modalOpen} onModalShown={handleShown} onDismiss={handleDismiss} views={views} />
  );
};

export default InfoModal;
