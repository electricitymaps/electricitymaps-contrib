import React, { useState, useEffect } from 'react';
import { connect } from 'react-redux';

import { useTranslation } from '../helpers/translation';
import { saveKey } from '../helpers/storage';
import { dispatchApplication } from '../store';
import { useTrackEvent } from '../hooks/tracking';

const views = [{
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
}, {
  headerImage: resolvePath('images/onboarding/mapExtract.png'),
  renderContent: (__) => (
    <React.Fragment>
      <div>
        <h2>{__('onboarding-modal.view2.header')}</h2>
      </div>
      <div>{__('onboarding-modal.view2.text')}</div>
    </React.Fragment>
  ),
}, {
  headerImage: resolvePath('images/onboarding/exchangeArrows.png'),
  renderContent: (__) => (
    <React.Fragment>
      <div>
        <h2>{__('onboarding-modal.view3.header')}</h2>
      </div>
      <div>{__('onboarding-modal.view3.text')}</div>
    </React.Fragment>
  ),
}, {
  headerImage: resolvePath('images/onboarding/splitLayers.png'),
  renderContent: (__) => (
    <React.Fragment>
      <div>
        <h2>{__('onboarding-modal.view4.header')}</h2>
      </div>
      <div>{__('onboarding-modal.view4.text')}</div>
    </React.Fragment>
  ),
}];

const mapStateToProps = state => ({
  // Show onboarding modal only if it's not been seen yet and if the app is not embedded
  visible: !state.application.onboardingSeen && !state.application.isEmbedded,
});

const OnboardingModal = ({ visible }) => {
  const trackEvent = useTrackEvent();
  const { __ } = useTranslation();

  const [currentViewIndex, setCurrentViewIndex] = useState(0);
  const isOnLastView = () => currentViewIndex === views.length - 1;
  const isOnFirstView = () => currentViewIndex === 0;

  const handleDismiss = () => {
    saveKey('onboardingSeen', true);
    dispatchApplication('onboardingSeen', true);
  };
  const handleBack = () => {
    if (!isOnFirstView()) {
      setCurrentViewIndex(currentViewIndex - 1);
    }
  };
  const handleForward = () => {
    if (!isOnLastView()) {
      setCurrentViewIndex(currentViewIndex + 1);
    }
  };

  // Dismiss the modal if SPACE key is pressed
  useEffect(() => {
    const keyPressHandlers = (ev) => {
      if (ev.keyCode === 32) {
        handleDismiss();
      }
    };
    document.addEventListener('keypress', keyPressHandlers);
    return () => {
      document.removeEventListener('keypress', keyPressHandlers);
    };
  });

  // Track event when the onboarding modal opens up
  useEffect(() => {
    if (visible) {
      trackEvent('onboardingModalShown');
    }
  }, [visible]);

  if (!visible) return null;

  return (
    <React.Fragment>
      <div className="modal-background-overlay" onClick={handleDismiss} />
      <div className="modal">
        <div className="modal-left-button-container">
          {!isOnFirstView() && (
            <div className="modal-left-button" onClick={handleBack}>
              <i className="material-icons">arrow_back</i>
            </div>
          )}
        </div>
        <div className="modal-body">
          <div className="modal-close-button-container">
            <div className="modal-close-button" onClick={handleDismiss}>
              <i className="material-icons">close</i>
            </div>
          </div>
          <div
            className={`modal-header ${views[currentViewIndex].headerCssClass || ''}`}
            style={{ backgroundImage: `url("${views[currentViewIndex].headerImage}")` }}
          />
          <div className={`modal-text ${views[currentViewIndex].textCssClass || ''}`}>
            {views[currentViewIndex].renderContent(__)}
          </div>
        </div>
        <div className="modal-footer">
          {views.map((view, index) => (
            <div
              key={view.headerImage}
              className={`modal-footer-circle ${index === currentViewIndex ? 'highlight' : ''}`}
            />
          ))}
        </div>
        <div className="modal-right-button-container">
          {isOnLastView() ? (
            <div className="modal-right-button green" onClick={handleDismiss}>
              <i className="material-icons">check</i>
            </div>
          ) : (
            <div className="modal-right-button" onClick={handleForward}>
              <i className="material-icons">arrow_forward</i>
            </div>
          )}
        </div>
      </div>
    </React.Fragment>
  );
};

export default connect(mapStateToProps)(OnboardingModal);
