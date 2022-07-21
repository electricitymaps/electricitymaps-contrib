import React from 'react';
import { useSelector } from 'react-redux';

import { useTranslation } from '../helpers/translation';
import { saveKey } from '../helpers/storage';
import { dispatchApplication } from '../store';
import { useTrackEvent } from '../hooks/tracking';
import { useSearchParams } from '../hooks/router';

import Modal from './modal';
import styled from 'styled-components';

const DateSubtitle = styled.small`
  color: #666;
`;

// TODO: Use proper text and images (also remember to run images through TinyPNG and a gif optimizer)
// Note: This content is not in translations on purpose, as it will only live a short while (1 month)
const views = [
  {
    headerImage: resolvePath('images/historicalviewmodal/step1_hw_modal.png'),
    renderContent: (__) => (
      <React.Fragment>
        <DateSubtitle>July 2022</DateSubtitle>
        <div>
          <h2>New feature: Historical View</h2>
        </div>
        <div>
          Dive deeper, explore and understand the evolution and variability of countries and regions all across the
          world on our common path towards low-carbon electricity systems.
        </div>
      </React.Fragment>
    ),
  },
  {
    headerImage: resolvePath('images/historicalviewmodal/step2_hw_modal.gif'),
    renderContent: (__) => (
      <React.Fragment>
        <div>
          <h2>Explore your slice of history</h2>
        </div>
        <div>
          In our updated time navigator, you can now select and scroll through a variety of different slices of time.
          The map and details panel will update accordingly and show you the state of the grid at that point in time.
        </div>
      </React.Fragment>
    ),
  },
  // temporarily disabled until we have all resources available
  // {
  //   headerImage: resolvePath('images/historicalviewmodal/step3_hw_modal.png'),
  //   renderContent: (__) => (
  //     <React.Fragment>
  //       <div>
  //         <h2>Want to learn more and contribute?</h2>
  //       </div>
  //       <div>
  //         We have created <a href="/">a YouTube explainer video</a>, written <a href="/">a blog post</a> and shared{' '}
  //         <a href="/">our metholodogy on GitHub</a>. If you have any feedback we&apos;d love to{' '}
  //         <a href="/">hear from you</a>!
  //       </div>
  //     </React.Fragment>
  //   ),
  // },
];

const HistoricalViewIntroModal = () => {
  const visible = useSelector(
    (state) => !state.application.historicalViewIntroModalSeen && !state.application.isEmbedded
  );
  const trackEvent = useTrackEvent();
  const { __ } = useTranslation();
  // Stop showing this modal a month after the feature is released
  const isExpired = new Date() > new Date('2022-08-18');
  // If user has skipped onboarding, also don't show this modal
  const shouldSkip = useSearchParams().get('skip-onboarding') === 'true';

  const shouldShowModal = visible && !shouldSkip && !isExpired;

  const handleDismiss = () => {
    saveKey('historicalViewIntroModalSeen', true);
    dispatchApplication('historicalViewIntroModalSeen', true);
  };

  const handleShown = () => {
    trackEvent('HistoricalViewIntroModal Shown');
  };

  return (
    <Modal
      modalName="historical-view-intro"
      visible={shouldShowModal}
      onModalShown={handleShown}
      onDismiss={handleDismiss}
      views={views}
    />
  );
};

export default HistoricalViewIntroModal;
