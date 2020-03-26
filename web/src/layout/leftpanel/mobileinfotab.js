/* eslint-disable jsx-a11y/label-has-for */
/* eslint-disable jsx-a11y/anchor-is-valid */
/* eslint-disable jsx-a11y/anchor-has-content */
/* eslint-disable react/jsx-no-target-blank */
// TODO: re-enable rules

import React from 'react';

import { __ } from '../../helpers/translation';
import FAQ from '../../components/faq';

const MobileInfoTab = () => (
  <div className="mobile-info-tab large-screen-hidden">
    <div className="mobile-watermark brightmode">
      <a href="http://www.tmrow.com/mission?utm_source=electricitymap.org&utm_medium=referral&utm_campaign=watermark" target="_blank">
        <img src="/images/built-by-tomorrow.svg" alt="" />
      </a>
      <div className="socialicons">
        <div
          className="fb-like"
          data-href="https://www.facebook.com/tmrowco"
          data-layout="button"
          data-action="like"
          data-size="small"
          data-show-faces="false"
        />
        <a
          className="twitter-follow-button"
          href="https://twitter.com/electricitymap"
          data-show-screen-name="false"
          data-show-count="false"
          data-lang={locale}
        />
      </div>
    </div>

    <div className="info-text">
      <p>
        <input type="checkbox" id="checkbox-colorblind" />
        <label htmlFor="checkbox-colorblind">
          {__('legends.colorblindmode')}
        </label>
      </p>
      <p>
        {__('panel-initial-text.thisproject')} <a href="https://github.com/tmrowco/electricitymap-contrib" target="_blank">{__('panel-initial-text.opensource')}</a> ({__('panel-initial-text.see')} <a href="https://github.com/tmrowco/electricitymap-contrib#data-sources" target="_blank">{__('panel-initial-text.datasources')}</a>). <span dangerouslySetInnerHTML={{ __html: __('panel-initial-text.contribute', 'https://github.com/tmrowco/electricitymap-contrib#adding-a-new-region') }} />.
      </p>
      <p>
        {__('footer.foundbugs')} <a href="https://github.com/tmrowco/electricitymap-contrib/issues/new" target="_blank">{__('footer.here')}</a>.<br />
      </p>
      <p>
        {__('footer.likethisvisu')} <a href="https://docs.google.com/forms/d/e/1FAIpQLSc-_sRr3mmhe0bifigGxfAzgh97-pJFcwpwWZGLFc6vvu8laA/viewform?c=0&w=1" target="_blank">{__('footer.loveyourfeedback')}</a>!
      </p>
    </div>
    <div className="social-buttons large-screen-hidden">
      <div>
        { /* Facebook share */}
        <div
          className="fb-share-button"
          data-href="https://www.electricitymap.org/"
          data-layout="button_count"
        />
        { /* Twitter share */}
        <a
          className="twitter-share-button"
          data-url="https://www.electricitymap.org"
          data-via="electricitymap"
          data-lang={locale}
        />
        { /* Slack */}
        <span className="slack-button">
          <a href="https://slack.tmrow.co" target="_blank" className="slack-btn">
            <span className="slack-ico" />
            <span className="slack-text">Slack</span>
          </a>
        </span>
      </div>
    </div>

    <div className="mobile-faq-header">
      {__('misc.faq')}
    </div>
    <FAQ className="mobile-faq" />
  </div>
);

export default MobileInfoTab;
