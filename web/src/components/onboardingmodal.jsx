import React from 'react';
import { connect } from 'react-redux';

import { useTranslation } from '../helpers/translation';
import { saveKey } from '../helpers/storage';
import { dispatchApplication } from '../store';
import { useTrackEvent } from '../hooks/tracking';
import { useSearchParams } from '../hooks/router';

import Modal from './modal';

const views = [
  {
    headerImage: resolvePath('images/onboarding/electricymapLogoIcon.svg'),
    headerCssClass: 'logo-header',
    textCssClass: 'brand-text',
    renderContent: (__) => (
      <React.Fragment>
        <div>
          <h1>electricityMap</h1>
        </div>
        <div>
          <h2>{__('onboarding-modal.view1.subtitle')}</h2>
        </div>
      </React.Fragment>
    ),
  },
  {
    headerImage: resolvePath('images/onboarding/mapExtract.png'),
    renderContent: (__) => (
      <React.Fragment>
        <div>
          <h2>{__('onboarding-modal.view2.header')}</h2>
        </div>
        <div>{__('onboarding-modal.view2.text')}</div>
      </React.Fragment>
    ),
  },
  {
    headerImage: resolvePath('images/onboarding/exchangeArrows.png'),
    renderContent: (__) => (
      <React.Fragment>
        <div>
          <h2>{__('onboarding-modal.view3.header')}</h2>
        </div>
        <div>{__('onboarding-modal.view3.text')}</div>
      </React.Fragment>
    ),
  },
  {
    headerImage: resolvePath('images/onboarding/splitLayers.png'),
    renderContent: (__) => (
      <React.Fragment>
        <div>
          <h2>{__('onboarding-modal.view4.header')}</h2>
        </div>
        <div>{__('onboarding-modal.view4.text')}</div>
      </React.Fragment>
    ),
  },
];

const mapStateToProps = (state) => ({
  // Show onboarding modal only if it's not been seen yet and if the app is not embedded
  visible: !state.application.onboardingSeen && !state.application.isEmbedded,
});

const OnboardingModal = ({ visible }) => {
  const trackEvent = useTrackEvent();
  const { __ } = useTranslation();
  const shouldSkip = useSearchParams().get('skip-onboarding') === 'true';

  const handleDismiss = () => {
    saveKey('onboardingSeen', true);
    dispatchApplication('onboardingSeen', true);
  };

  const handleShown = () => {
    trackEvent('Onboarding Shown');
  };

  const isDisabled = new Date() < new Date('2022-08-12');

  return (
    <Modal
      modalName="onboarding"
      visible={visible && !shouldSkip && !isDisabled}
      onModalShown={handleShown}
      onDismiss={handleDismiss}
      views={views}
    />
  );
};

export default connect(mapStateToProps)(OnboardingModal);
