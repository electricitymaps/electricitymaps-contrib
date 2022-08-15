import React from 'react';
import { connect } from 'react-redux';
import { Link, Redirect, useLocation } from 'react-router-dom';

import { useTranslation } from '../../helpers/translation';
import FAQ from '../../components/faq';
import Icon from '../../components/icon';

const mapStateToProps = (state) => ({
  isMobile: state.application.isMobile,
});

const FAQPanel = ({ isMobile }) => {
  const { __ } = useTranslation();
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
        <Link to={parentPage} className="left-panel-back-button">
          <Icon iconName="arrow_back" />
        </Link>
        <span className="title">{__('misc.faq')}</span>
      </div>
      <FAQ className="faq" />
    </div>
  );
};

export default connect(mapStateToProps)(FAQPanel);
