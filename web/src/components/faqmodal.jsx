import React from 'react';
import { dispatchApplication } from '../store';
import { useTrackEvent } from '../hooks/tracking';

import FAQ from './faq';
import { useSelector } from 'react-redux';
import Modal from './modal';
import styled from 'styled-components';
import Icon from './icon';

const MobileFAQ = styled(FAQ)`
  text-align: left;
  .faq-container {
    max-height: 75vh;
    overflow-y: scroll;
    padding-right: 1rem;
  }
  .title {
    font-weight: bold;
    font-size: 1rem;
  }
`;

const BackButtonWrapper = styled.div`
  position: absolute;
  padding: 14px;
  left: 0;
  top: 0;
`;

const Title = ({ title }) => {
  const handleClick = () => {
    dispatchApplication('faqModalOpen', false);
  };

  return (
    <React.Fragment>
      <BackButtonWrapper>
        <div className="modal-back-button" onClick={handleClick}>
          <Icon iconName="arrow_back" />
        </div>
      </BackButtonWrapper>
      {title}
    </React.Fragment>
  );
};

const views = [
  {
    title: (__) => <Title title={__('misc.faq')} />,
    renderContent: (__) => <MobileFAQ className="mobile-faq" />,
  },
];

const FAQModal = () => {
  const modalOpen = useSelector((state) => state.application.faqModalOpen);
  const trackEvent = useTrackEvent();

  const handleDismiss = () => {
    dispatchApplication('faqModalOpen', false);
  };

  const handleShown = () => {
    trackEvent('FAQ Modal Shown');
  };

  return (
    <Modal modalName="FAQ" visible={modalOpen} onModalShown={handleShown} onDismiss={handleDismiss} views={views} />
  );
};

export default FAQModal;
