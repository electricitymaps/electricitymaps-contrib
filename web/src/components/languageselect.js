import React, { useState } from 'react';
import { map } from 'lodash';

import { __ } from '../helpers/translation';
import { languageNames } from '../../locales-config.json';

import ButtonToggle from './buttontoggle';

const LanguageSelect = () => {
  const [languagesVisible, setLanguagesVisible] = useState(false);
  const toggleLanguagesVisible = () => {
    setLanguagesVisible(!languagesVisible);
  };

  const handleLanguageSelect = (key) => {
    window.location.href = window.isCordova ? `index_${key}.html` : `${window.location.href}&lang=${key}`;
  };

  return (
    <div>
      <ButtonToggle
        onChange={toggleLanguagesVisible}
        tooltip={__('tooltips.selectLanguage')}
        icon="language_select"
      />
      {languagesVisible && (
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

export default LanguageSelect;
