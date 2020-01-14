import React, { useState } from 'react';
import { connect } from 'react-redux';
import { map } from 'lodash';

import { __ } from '../helpers/translation';
import { languageNames } from '../../locales-config.json';

const mapStateToProps = state => ({
  isMobile: state.application.isMobile,
});

const LanguageSelect = ({ isMobile }) => {
  const [showLanguages, setShowLanguages] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  // Mouseovers will trigger on click on mobile and is therefore only set on desktop
  const handleMouseOver = () => {
    if (!isMobile) setShowTooltip(true);
  };
  const handleMouseOut = () => {
    if (!isMobile) setShowTooltip(false);
  };
  const handleClick = () => {
    setShowLanguages(!showLanguages);
  };
  const handleLanguageSelect = (key) => {
    window.location.href = window.isCordova ? `index_${key}.html` : `${window.location.href}&lang=${key}`;
  };

  return (
    <div>
      <button
        type="button"
        className="layer-button language-select-button"
        onClick={handleClick}
        onFocus={handleMouseOver}
        onMouseOver={handleMouseOver}
        onMouseOut={handleMouseOut}
        onBlur={handleMouseOut}
      />
      {showTooltip && (
        <div id="language-select-button-tooltip" className="layer-button-tooltip">
          <div className="tooltip-container">
            <div className="tooltip-text">{__('tooltips.selectLanguage')}</div>
            <div className="arrow" />
          </div>
        </div>
      )}
      {showLanguages && (
        <div id="language-select-container">
          {map(languageNames, (language, key) => (
            <li key={key} onClick={() => handleLanguageSelect(key)}>
              {language}
            </li>
          ))}
        </div>
      )}
    </div>
  );
};

export default connect(mapStateToProps)(LanguageSelect);
