import React, { useState } from 'react';
import { map } from 'lodash';

import { useTranslation } from '../helpers/translation';
import { LANGUAGE_NAMES } from '../helpers/constants';
import styled from 'styled-components';

import ButtonToggle from './buttontoggle';

const LanguageSelectContainer = styled.div`
  background-color: #fafafa;
  color: black;
  border-radius: 4px;
  font-size: 0.9rem;
  padding: 5px 10px;
  box-shadow: 0px 0px 10px 0px rgba(0, 0, 0, 0.15);
  position: absolute;
  left: -184px;
  width: 150px;
  top: 4px;
  visibility: visible;
  opacity: 1;
  transform: translateX(0px);
  transition: opacity 0.4s, visibility 0.4s, transform 0.4s;

  #close-language-select-container {
    display: none;
  }

  @media (max-width: 700px) {
    position: fixed;
    width: 100%;
    height: 100%;
    left: 0;
    top: 0;
    z-index: 100;
    text-align: center;
    overflow-y: scroll;
    #close-language-select-container {
      display: block;
      position: fixed;
    }
  }

  &.hidden {
    visibility: hidden;
    opacity: 0;
    transform: translateX(10px);
  }

  li {
    margin: 0;
    padding: 0;
    list-style: none;

    &:hover {
      cursor: pointer;
    }
  }
`;

const LanguageSelect = () => {
  const [languagesVisible, setLanguagesVisible] = useState(false);
  const { __, i18n } = useTranslation();

  const toggleLanguagesVisible = () => {
    setLanguagesVisible(!languagesVisible);
  };

  const handleLanguageSelect = (languageKey) => {
    i18n.changeLanguage(languageKey);
    setLanguagesVisible(false);
  };

  return (
    <div>
      <ButtonToggle
        onChange={toggleLanguagesVisible}
        tooltip={__('tooltips.selectLanguage')}
        ariaLabel={__('tooltips.selectLanguage')}
        icon="language_select"
      />
      {languagesVisible && (
        <LanguageSelectContainer className="language-select-container">
          <div id="close-language-select-container">
            <ButtonToggle
              onChange={toggleLanguagesVisible}
              tooltip={__('tooltips.selectLanguage')}
              ariaLabel={__('tooltips.selectLanguage')}
              icon="language_select"
            />
          </div>
          {map(LANGUAGE_NAMES, (language, key) => (
            <li key={key} onClick={() => handleLanguageSelect(key)}>
              {language}
            </li>
          ))}
        </LanguageSelectContainer>
      )}
    </div>
  );
};

export default LanguageSelect;
