import React, { useState } from 'react';

import { useTranslation } from '../helpers/translation';
import { LANGUAGE_NAMES } from '../helpers/constants';
import styled from 'styled-components';

import ButtonToggle from './buttontoggle';

const LanguageSelectContainer = styled.ul`
  background-color: #fafafa;
  color: black;
  border-radius: 4px;
  font-size: 0.9rem;
  padding: 5px 0px;
  margin-top: 0;
  box-shadow: 0px 0px 10px 0px rgba(0, 0, 0, 0.15);
  position: absolute;
  left: -190px;
  width: 175px;
  visibility: visible;
  opacity: 1;
  transform: translateX(0px);
  transition: opacity 0.4s, visibility 0.4s, transform 0.4s;
  z-index: 99;
  min-height: 19.5rem;
  height: 100%;
  overflow-x: auto;
  list-style: none;
  &.hidden {
    visibility: hidden;
    opacity: 0;
    transform: translateX(10px);
  }
  button {
    width: 100%;
    background: transparent;
    border: 0;
    padding: 8px;
    cursor: pointer;
    text-align: left;
    &:hover {
      background-color: rgba(0, 0, 0, 0.05);
    }
    &.preferred-language {
      background-color: rgba(0, 0, 0, 0.1);
      position: absolute;
      top: 0;
    }
    &.other-language {
      position: relative;
      top: 27px;
    }
  }
`;

const LanguageSelect = () => {
  const [languagesVisible, setLanguagesVisible] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState('English');
  const { __, i18n } = useTranslation();

  const toggleLanguagesVisible = () => {
    setLanguagesVisible(!languagesVisible);
  };

  const handleLanguageSelect = (languageKey, preferredLanguage) => {
    i18n.changeLanguage(languageKey);
    setSelectedLanguage(preferredLanguage);
    setLanguagesVisible(false);
  };

  return (
    <>
      <ButtonToggle
        onChange={toggleLanguagesVisible}
        tooltip={__('tooltips.selectLanguage')}
        ariaLabel={__('tooltips.selectLanguage')}
        icon="language_select"
      />
      {languagesVisible && (
        <LanguageSelectContainer className="language-select-container">
          {Object.entries(LANGUAGE_NAMES).map(([key, language]) => (
            <li key={key}>
              <button
                onClick={() => handleLanguageSelect(key, language)}
                className={selectedLanguage === language ? 'preferred-language' : 'other-language'}
              >
                {language}
              </button>
            </li>
          ))}
        </LanguageSelectContainer>
      )}
    </>
  );
};

export default LanguageSelect;
