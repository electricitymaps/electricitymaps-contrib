import React from 'react';
import { connect } from 'react-redux';
import { Link, Redirect, useLocation } from 'react-router-dom';

import { __ } from '../../helpers/translation';
import FAQ from '../../components/faq';

const mapStateToProps = state => ({
  isMobile: state.application.isMobile,
});

const FAQPanel = ({ isMobile }) => {
  const location = useLocation();
  const parentPage = {
    pathname: isMobile ? '/info' : '/map',
    search: location.search,
  };

  // FAQ section is embedded on the /info page on mobile screens
  if (isMobile) {
    return <Redirect to={parentPage} />;
  }

  return (
    <div className="faq-panel">
      <div className="faq-header">
        <Link to={parentPage}>
          <span className="left-panel-back-button">
            <i className="material-icons" aria-hidden="true">arrow_back</i>
          </span>
        </Link>
        <span className="title">{__('misc.faq')}</span>
      </div>
      <FAQ className="faq" />
    </div>
  );
};

export default connect(mapStateToProps)(FAQPanel);
