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

const views = [
  {
    headerImage: resolvePath('images/historicalviewmodal/timeslider.png'),
    renderContent: (__) => (
      <React.Fragment>
        <DateSubtitle>July 2022</DateSubtitle>
        <div>
          <h2>Introducing the new historical view</h2>
        </div>
        <div>
          You can now explore how countries and regions have changed over time by diving into the historical view of the
          map.
        </div>
      </React.Fragment>
    ),
  },
  {
    headerImage: resolvePath('images/historicalviewmodal/timeslider.png'),
    renderContent: (__) => (
      <React.Fragment>
        <div>
          <h2>How to use it</h2>
        </div>
        <div>
          In the left corner (or bottom of your screen on a phone) you can choose between seeing the last 24 hours as
          before, or select a monthly, yearly or 5 year aggregate for every single area that we have data for.
        </div>
      </React.Fragment>
    ),
  },
  {
    headerImage: resolvePath('images/historicalviewmodal/timeslider.png'),
    renderContent: (__) => (
      <React.Fragment>
        <div>
          <h2>Want to learn more about how and why this new feature came to be?</h2>
        </div>
        <div>
          We have created <a href="">a YouTube explainer video</a>, written <a href="">a blog post</a> and shared{' '}
          <a href="">our metholodogy on GitHub</a>. If you have any feedback (good and/or bad!) we&apos;d love to{' '}
          <a href="">hear from you</a>!
        </div>
      </React.Fragment>
    ),
  },
  //   {
  //     headerImage: resolvePath('images/onboarding/splitLayers.png'),
  //     renderContent: (__) => (
  //       <React.Fragment>
  //         <div>
  //           <h2>Go explore!</h2>
  //         </div>
  //         <div>
  //           Otherwise you should just go explore how the electricity grids are changing throughout time and across the
  //           globe! For example, you could check out how fast <a href="#">Spain is getting rid of coal</a> or{' '}
  //           <a href="#">see an example of seasonality</a>.
  //         </div>
  //       </React.Fragment>
  //     ),
  //   },
];

const HistoricalViewIntroModal = () => {
  const visible = useSelector(
    (state) => !state.application.historicalViewIntroModalSeen && !state.application.isEmbedded
  );
  const trackEvent = useTrackEvent();
  const { __ } = useTranslation();
  // Stop showing this modal a month after the feature is released
  const isExpired = new Date() > new Date('2022-08-12');

  // If user has skipped onboarding, also don't show this modal
  // TODO: This parameter should ideally be called something else (e.g. "kiosk", "tv-mode" or similar)
  // but we currently have users relying on existing naming
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
