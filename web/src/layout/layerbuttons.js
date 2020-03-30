import React from 'react';

import LanguageSelect from '../components/languageselect';

// Modules
import { __ } from '../helpers/translation';

export default () => (
  <div className="layer-buttons-container">
    <LanguageSelect />
    <div>
      <button type="button" className="layer-button wind-button" />
      <div id="wind-layer-button-tooltip" className="layer-button-tooltip hidden">
        <div className="tooltip-container">
          <div className="tooltip-text">{__('tooltips.showWindLayer')}</div>
          <div className="arrow" />
        </div>
      </div>
    </div>
    <div>
      <button type="button" className="layer-button solar-button" />
      <div id="solar-layer-button-tooltip" className="layer-button-tooltip hidden">
        <div className="tooltip-container">
          <div className="tooltip-text">{__('tooltips.showSolarLayer')}</div>
          <div className="arrow" />
        </div>
      </div>
    </div>
    <div>
      <button type="button" className="layer-button brightmode-button" />
      <div id="brightmode-layer-button-tooltip" className="layer-button-tooltip hidden">
        <div className="tooltip-container">
          <div className="tooltip-text">{__('tooltips.toggleDarkMode')}</div>
          <div className="arrow" />
        </div>
      </div>
    </div>
  </div>
);
