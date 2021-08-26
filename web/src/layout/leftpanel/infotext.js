/* eslint-disable jsx-a11y/click-events-have-key-events */
/* eslint-disable jsx-a11y/anchor-is-valid */
/* eslint-disable jsx-a11y/anchor-has-content */
/* eslint-disable react/jsx-no-target-blank */
// TODO: re-enable rules

import React from 'react';
import { Link, useLocation } from 'react-router-dom';

import { __ } from '../../helpers/translation';
import ColorBlindCheckbox from '../../components/colorblindcheckbox';

export default () => (
  <div className="info-text small-screen-hidden">
    <ColorBlindCheckbox />
    <p>
      {__('panel-initial-text.thisproject')}
      {' '}
      <a href="https://github.com/tmrowco/electricitymap-contrib" target="_blank">
        {__('panel-initial-text.opensource')}
      </a>
      {' '}(
      {__('panel-initial-text.see')}
      {' '}
      <a href="https://github.com/tmrowco/electricitymap-contrib/blob/master/DATA_SOURCES.md" target="_blank">
        {__('panel-initial-text.datasources')}
      </a>
      ).{' '}
      <span
        dangerouslySetInnerHTML={{
          __html: __(
            'panel-initial-text.contribute',
            'https://github.com/tmrowco/electricitymap-contrib/wiki/Getting-started',
          ),
        }}
      />
      .
    </p>
    <p>
      {__('footer.foundbugs')} <a href="https://github.com/tmrowco/electricitymap-contrib/issues/new" target="_blank">{__('footer.here')}</a>.<br />
    </p>
    <p>
      {__('footer.faq-text')}
      {' '}
      <Link to={{ pathname: '/faq', search: useLocation().search }}>
        <span className="faq-link">{__('footer.faq')}</span>
      </Link>
    </p>
    <div className="social-buttons">
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
          <a href="https://slack.tmrow.com" target="_blank" className="slack-btn">
            <span className="slack-ico" />
            <span className="slack-text">Slack</span>
          </a>
        </span>
      </div>
    </div>
  </div>
);
