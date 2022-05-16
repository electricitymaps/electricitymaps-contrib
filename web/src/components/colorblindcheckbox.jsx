/* eslint-disable jsx-a11y/label-has-for */
/* eslint-disable jsx-a11y/label-has-associated-control */
import React from 'react';
import { useSelector } from 'react-redux';

import { dispatchApplication } from '../store';
import { saveKey } from '../helpers/storage';
import { useTranslation } from '../helpers/translation';

const ColorBlindCheckbox = () => {
  const { __ } = useTranslation();
  const colorBlindModeEnabled = useSelector((state) => state.application.colorBlindModeEnabled);
  const toggleColorBlindMode = () => {
    dispatchApplication('colorBlindModeEnabled', !colorBlindModeEnabled);
    saveKey('colorBlindModeEnabled', !colorBlindModeEnabled);
  };

  return (
    <p>
      <label className="checkbox-container">
        {__('legends.colorblindmode')}
        <input
          type="checkbox"
          id="checkbox-colorblind"
          checked={colorBlindModeEnabled}
          onChange={toggleColorBlindMode}
        />
        <span className="checkmark" />
      </label>
    </p>
  );
};

export default ColorBlindCheckbox;
