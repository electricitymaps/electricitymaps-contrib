import React from 'react';

import { __ } from '../../helpers/translation';
import { navigateToPath } from '../../helpers/router';
import FAQ from '../../components/faq';

const FAQPanel = () => (
  <div className="faq-panel">
    <div className="faq-header">
      <span className="left-panel-back-button" onClick={() => navigateToPath('/map')}>
        <i className="material-icons" aria-hidden="true">arrow_back</i>
      </span>
      <span className="title">{__('misc.faq')}</span>
    </div>
    <FAQ className="faq" />
  </div>
);

export default FAQPanel;
