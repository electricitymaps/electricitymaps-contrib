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

const Title = ({ title }: any) => {
  const handleClick = () => {
    dispatchApplication('faqModalOpen', false);
  };

  return (
    <React.Fragment>
      <BackButtonWrapper>
        <button className="modal-back-button" onClick={handleClick}>
          <Icon iconName="arrow_back" />
        </button>
      </BackButtonWrapper>
      {title}
    </React.Fragment>
  );
};

const views = [
  {
    title: (__: any) => <Title title={__('misc.faq')} />,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    renderContent: (__: any) => <MobileFAQ className="mobile-faq" />,
  },
];

const FAQModal = () => {
  const modalOpen = useSelector((state) => (state as any).application.faqModalOpen);
  const trackEvent = useTrackEvent();

  const handleDismiss = () => {
    dispatchApplication('faqModalOpen', false);
  };

  const handleShown = () => {
    // @ts-expect-error TS(2554): Expected 2 arguments, but got 1.
    trackEvent('FAQ Modal Shown');
  };

  return (
    <Modal modalName="FAQ" visible={modalOpen} onModalShown={handleShown} onDismiss={handleDismiss} views={views} />
  );
};

export default FAQModal;
