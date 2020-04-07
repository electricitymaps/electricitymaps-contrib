import React from 'react';
import { Link, useLocation } from 'react-router-dom';

import { __ } from '../../helpers/translation';
import FAQ from '../../components/faq';

const FAQPanel = () => (
  <div className="faq-panel">
    <div className="faq-header">
      <Link to={{ pathname: '/map', search: useLocation().search }}>
        <span className="left-panel-back-button">
          <i className="material-icons" aria-hidden="true">arrow_back</i>
        </span>
      </Link>
      <span className="title">{__('misc.faq')}</span>
    </div>
    <FAQ className="faq" />
  </div>
);

export default FAQPanel;
