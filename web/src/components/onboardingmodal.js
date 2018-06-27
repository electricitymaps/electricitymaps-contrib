const translation = require('../helpers/translation');
const formatting = require('../helpers/formatting');
const d3 = Object.assign(
  {},
  require('d3-selection'),
);

const SPACE_KEY_CODE = 32;

const defaultViews = [{
  headerImage: 'images/onboarding/electricymapLogoIcon.svg',
  headerCssClass: 'logo-header',
  textCssClass: 'brand-text',
  textHtml: `<div><h1>electricityMap</h1></div>
      <div><h2>${translation.translate('onboarding-modal.view1.subtitle')}</h2></div>`,
},
{
  headerImage: 'images/onboarding/mapExtract.png',
  textHtml: `<div><h2>${formatting.co2Sub(translation.translate('onboarding-modal.view2.header'))}</h2></div>
      <div>${translation.translate('onboarding-modal.view2.text')}</div>`,
}, {
  headerImage: 'images/onboarding/exchangeArrows.png',
  textHtml: `<div><h2>${translation.translate('onboarding-modal.view3.header')}</h2></div> 
      <div>${translation.translate('onboarding-modal.view3.text')}</div>`,
},
{
  headerImage: 'images/onboarding/splitLayers.png',
  textHtml: `<div><h2>${translation.translate('onboarding-modal.view4.header')}</h2></div>
      <div>${translation.translate('onboarding-modal.view4.text')}</div>`,
},
];


export default class OnboardingModal {
  constructor(selectorId, argConfig) {
    const config = argConfig || {};
    this.views = config.views || defaultViews;
    this.dismissHandler = config.dismissHandler || (() => undefined);

    this.selectorId = selectorId;
    this.currentViewIndex = 0;
    this._setupSpaceKeypressDismiss();
    this._setupLayout();
  }

  onDismiss(dismissHandler) {
    this.dismissHandler = dismissHandler;
  }

  dismiss() {
    this.dismissHandler();
    this._hideRootContainer();
    this._removeBackgroundOverlay();
  }

  render() {
    this._updateBody();
    this._updateSideButtons();
    this._updateFooter();
  }

  showPreviousView() {
    if (this.currentViewIndex > 0) {
      this.currentViewIndex -= 1;
      this.render();
    } else {
      throw new Error('Cannot show previous view: No more views to show');
    }
  }

  showNextView() {
    if (this.views.length - 1 > this.currentViewIndex) {
      this.currentViewIndex += 1;
      this.render();
    } else {
      throw new Error('Cannot show next view: No more views to show');
    }
  }

  _setupSpaceKeypressDismiss() {
    document.addEventListener('keypress', (e) => {
      if (e.keyCode === SPACE_KEY_CODE) {
        this.dismiss();
      }
    });
  }

  _setupLayout() {
    this._setupBackgroundOverlay();
    this._setupRootContainer();
    this._setupLeftButton();
    this._setupBody();
    this._setupFooter();
    this._setupRightButton();
    this.render();
  }

  _setupBackgroundOverlay() {
    this.backgroundOverlay = d3.select(this.selectorId).append('div').attr('class', 'modal-background-overlay');
  }

  _setupRootContainer() {
    this.rootContainer = d3.select(this.selectorId).append('div').attr('class', 'modal');
  }

  _hideRootContainer() {
    this.rootContainer.attr('style', 'display: none');
  }

  _removeBackgroundOverlay() {
    this.backgroundOverlay.remove();
  }

  _setupLeftButton() {
    const leftButtonContainer = this.rootContainer.append('div').attr('class', 'modal-left-button-container');
    this.leftButton = leftButtonContainer.append('div').attr('class', 'modal-left-button');
    this.leftButton.append('i').attr('class', 'material-icons').text('arrow_back');
    this.leftButton.on('click', () => this.showPreviousView());
  }

  _setupRightButton() {
    const rightButtonContainer = this.rootContainer.append('div').attr('class', 'modal-right-button-container');
    this.rightButton = rightButtonContainer.append('div').attr('class', 'modal-right-button');
    this.rightButton.append('i').attr('class', 'material-icons');
    this.rightButton.on('click', () => {
      if (this._modalIsAtLastView()) {
        this.dismiss();
      } else {
        this.showNextView();
      }
    });
  }

  _setupBody() {
    this.modalBody = this.rootContainer.append('div').attr('class', 'modal-body');
  }

  _setupFooter() {
    this.modalFooter = this.rootContainer.append('div').attr('class', 'modal-footer');
    this.modalFooterCircles = [];
    for (let i = 0; i < this.views.length; i += 1) {
      this.modalFooterCircles[i] = this.modalFooter.append('div').attr('class', 'modal-footer-circle');
    }
    this.modalFooterCircles[0].classed('highlight', true);
  }
  _updateBody() {
    this.modalBody.html(null);

    const currentView = this.views[this.currentViewIndex];

    this.modalBody.append('div').attr('class', `modal-header ${currentView.headerCssClass || ''}`)
      .style('background-image', `url("${currentView.headerImage}")`);

    this.modalBody.append('div').attr('class', `modal-text ${currentView.textCssClass || ''}`)
      .html(currentView.textHtml);
  }

  _updateSideButtons() {
    this.leftButton.classed('hidden', this._modalIsAtFirstView());

    this.rightButton.select('i').text(this._modalIsAtLastView() ? 'check' : 'arrow_forward');
    this.rightButton.classed('green', this._modalIsAtLastView());
  }


  _updateFooter() {
    for (let i = 0; i < this.modalFooterCircles.length; i += 1) {
      this.modalFooterCircles[i].classed('highlight', i === this.currentViewIndex);
    }
  }

  _modalIsAtFirstView() {
    return this.currentViewIndex === 0;
  }

  _modalIsAtLastView() {
    return this.currentViewIndex === this.views.length - 1;
  }
}
