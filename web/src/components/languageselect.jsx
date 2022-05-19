import React, { useState } from 'react';

import { useTranslation } from '../helpers/translation';
import { LANGUAGE_NAMES } from '../helpers/constants';
import styled from 'styled-components';

import ButtonToggle from './buttontoggle';

const LanguageSelectContainer = styled.div`
  background-color: #fafafa;
  color: black;
  border-radius: 4px;
  font-size: 0.9rem;
  padding: 5px 0px;
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
  &.hidden {
    visibility: hidden;
    opacity: 0;
    transform: translateX(10px);
  }

  li {
    margin: 0;
    padding: 5px 10px;
    list-style: none;

    &:hover {
      cursor: pointer;
      background-color: rgba(0, 0, 0, 0.05);
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
            <li key={key} onClick={() => handleLanguageSelect(key)}>
              {language}
            </li>
          ))}
        </LanguageSelectContainer>
      )}
    </>
  );
};

export default LanguageSelect;
