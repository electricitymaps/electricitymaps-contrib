import React from 'react';
import { useSelector } from 'react-redux';

import { dispatchApplication } from '../store';
import { saveKey } from '../helpers/storage';
import { useTranslation } from '../helpers/translation';
import styled from 'styled-components';

/* 
    custom "color blind mode" checkbox and others
    adopted with tweeks from source: https://www.w3schools.com/howto/howto_css_custom_checkbox.asp 
*/
const CheckboxContainer = styled.label`
  display: block;
  position: relative;
  padding-left: 28px;
  margin-bottom: 14px;
  font-size: 18px;
  cursor: pointer;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;

  /* Hide the browser's default checkbox */
  input {
    position: absolute;
    opacity: 0;
    cursor: pointer;
    height: 0;
    width: 0;
  }

  /* On mouse-over, add a grey background color */
  &:hover input ~ .checkmark {
    background-color: #ccc;
  }

  /* When the checkbox is checked, add a blue background */
  input:checked ~ .checkmark {
    background-color: #074ddb;
  }

  /* Show the checkmark when checked */
  input:checked ~ .checkmark:after {
    display: block;
  }
`;

const Checkmark = styled.span`
  position: absolute;
  top: 0;
  left: 0;
  height: 21px;
  width: 21px;
  border-radius: 6px;
  background-color: #eee;

  &:after {
    content: '';
    position: absolute;
    display: none;
    left: 7px;
    top: 4px;
    width: 4px;
    height: 8px;
    border: solid white;
    border-width: 0 3px 3px 0;
    -webkit-transform: rotate(45deg);
    -ms-transform: rotate(45deg);
    transform: rotate(45deg);
  }
`;

const ColorBlindCheckbox = () => {
  const { __ } = useTranslation();
  const colorBlindModeEnabled = useSelector((state) => state.application.colorBlindModeEnabled);
  const toggleColorBlindMode = () => {
    dispatchApplication('colorBlindModeEnabled', !colorBlindModeEnabled);
    saveKey('colorBlindModeEnabled', !colorBlindModeEnabled);
  };

  return (
    <p>
      <CheckboxContainer>
        {__('legends.colorblindmode')}
        <input
          type="checkbox"
          id="checkbox-colorblind"
          checked={colorBlindModeEnabled}
          onChange={toggleColorBlindMode}
        />
        <Checkmark className="checkmark" />
      </CheckboxContainer>
    </p>
  );
};

export default ColorBlindCheckbox;
