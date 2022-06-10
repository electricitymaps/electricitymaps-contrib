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
        <Button href="https://forms.gle/VHaeHzXyGodFKZY18" icon="comment" bgColor="#44AB60" textColor="#fff">
          {__('info-modal.feedback-button')}
        </Button>
        <Button
          href="https://github.com/electricitymap/electricitymap-contrib"
          icon="github"
          bgColor="linear-gradient(to right, #04275c 0%, #040e23 100%);"
          textColor="#fff"
        >
          {__('info-modal.github-button')}
        </Button>
        <Button
          href="https://twitter.com/intent/tweet?url=https://www.app.electricitymap.org"
          icon="twitter"
          bgColor="#1D9BF0"
          textColor="white"
        >
          {__('info-modal.twitter-button')}
        </Button>
        <Button href="https://slack.electricitymap.org/" icon="slack" bgColor="#4A154B" textColor="white">
          {__('info-modal.slack-button')}
        </Button>
      </div>
      <TermsAndPrivacyContainer>
        <a href="https://www.electricitymap.org/privacy-policy/">{__('info-modal.privacy-policy')}</a>
        <a href="https://www.electricitymap.org/legal-notice/">{__('info-modal.legal-notice')}</a>
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
