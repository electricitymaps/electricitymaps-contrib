import React, { useState } from 'react';
import { map } from 'lodash';

import { __ } from '../helpers/translation';
import { useSearchParams } from '../hooks/router';
import { languageNames } from '../../locales-config.json';

import ButtonToggle from './buttontoggle';

const LanguageSelect = () => {
  const [languagesVisible, setLanguagesVisible] = useState(false);
  const toggleLanguagesVisible = () => {
    setLanguagesVisible(!languagesVisible);
  };

  const searchParams = useSearchParams();
  const handleLanguageSelect = (languageKey) => {
    // TODO: Figure a better way to switch between languages that doesn't require a page refresh.
    // See https://github.com/tmrowco/electricitymap-contrib/issues/2382.
    if (window.isCordova) {
      window.location.href = `index_${languageKey}.html`;
    } else {
      searchParams.set('lang', languageKey);
      window.location.search = `?${searchParams.toString()}`;
    }
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
