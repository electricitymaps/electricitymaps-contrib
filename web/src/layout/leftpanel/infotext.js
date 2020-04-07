/* eslint-disable jsx-a11y/click-events-have-key-events */
/* eslint-disable jsx-a11y/anchor-is-valid */
/* eslint-disable jsx-a11y/anchor-has-content */
/* eslint-disable react/jsx-no-target-blank */
/* eslint-disable jsx-a11y/label-has-for */
/* eslint-disable jsx-a11y/label-has-associated-control */
// TODO: re-enable rules

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { connect } from 'react-redux';

// Modules
import { __ } from '../../helpers/translation';
import { updateApplication } from '../../actioncreators';

const mapStateToProps = state => ({});
const mapDispatchToProps = dispatch => ({
  dispatchApplication: (k, v) => dispatch(updateApplication(k, v)),
});

export default connect(mapStateToProps, mapDispatchToProps)(({ dispatchApplication }) => (
  <div className="info-text small-screen-hidden">
    <p>
      <label className="checkbox-container">
        {__('legends.colorblindmode')}
        <input type="checkbox" id="checkbox-colorblind" />
        <span className="checkmark" />
      </label>
    </p>
    <p>
      {__('panel-initial-text.thisproject')}
      {' '}
      <a href="https://github.com/tmrowco/electricitymap-contrib" target="_blank">
        {__('panel-initial-text.opensource')}
      </a>
      {' ('}
      {__('panel-initial-text.see')}
      {' '}
      <a href="https://github.com/tmrowco/electricitymap-contrib#data-sources" target="_blank">
        {__('panel-initial-text.datasources')}
      </a>
      {'). '}
      <span
        dangerouslySetInnerHTML={{
          __html: __(
            'panel-initial-text.contribute',
            'https://github.com/tmrowco/electricitymap-contrib#adding-a-new-region'
          ),
        }}
      />
      {'.'}
    </p>
    <p>
      {__('footer.foundbugs')} <a href="https://github.com/tmrowco/electricitymap-contrib/issues/new" target="_blank">{__('footer.here')}</a>.<br />
    </p>
    <p>
      {__('footer.likethisvisu')} <a href="https://docs.google.com/forms/d/e/1FAIpQLSc-_sRr3mmhe0bifigGxfAzgh97-pJFcwpwWZGLFc6vvu8laA/viewform?c=0&w=1" target="_blank">{__('footer.loveyourfeedback')}</a>!
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
          <a href="https://slack.tmrow.co" target="_blank" className="slack-btn">
            <span className="slack-ico" />
            <span className="slack-text">Slack</span>
          </a>
        </span>
      </div>
    </div>
  </div>
));
