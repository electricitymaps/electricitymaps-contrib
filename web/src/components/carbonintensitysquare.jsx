import React from 'react';
import styled from 'styled-components';

import { useCo2ColorScale } from '../hooks/theme';
import { useTranslation } from '../helpers/translation';

/**
 * This function finds the optimal text color based on a custom formula
 * derived from the W3CAG standard (see https://www.w3.org/TR/WCAG20-TECHS/G17.html).
 * I changed the original formula from Math.sqrt(1.05 * 0.05) - 0.05 to
 * Math.sqrt(1.05 * 0.18) - 0.05. Because this expression is a constant
 * I replaced it with it's approached value (0.3847...) to avoid useless computations.
 * See https://github.com/tmrowco/electricitymap-contrib/issues/3365 for more informations.
 * @param {string} rgbColor a string with the background color (e.g. "rgb(0,5,4)")
 */
const getTextColor = (rgbColor) => {
  const colors = rgbColor.replace(/[^\d,.]/g, '').split(',');
  const r = parseInt(colors[0], 10);
  const g = parseInt(colors[1], 10);
  const b = parseInt(colors[2], 10);
  const rgb = [r, g, b].map((c) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  });
  const luminosity = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2];
  return luminosity >= 0.38474130238568316 ? 'black' : 'white';
};

const Value = styled.span`
  font-weight: bold;
`;

const Box = styled.div`
  background-color: ${(props) => props.color};
  color: ${(props) => getTextColor(props.color)};
  display: flex;
  align-items: center;
  flex-direction: column;
  justify-content: center;
  height: 4rem;
  width: 4rem;
  margin: 0 auto;
  border-radius: 1rem;
  font-size: 1rem;
`;

const CarbonIntensitySquare = ({ value, withSubtext }) => {
  const { __ } = useTranslation();
  const co2ColorScale = useCo2ColorScale();

  return (
    <div className="country-col">
      <Box color={co2ColorScale(value)}>
        <div>
          <Value>{Math.round(value) || '?'}</Value>g
        </div>
      </Box>
      <div className="country-col-headline">{__('country-panel.carbonintensity')}</div>
      {withSubtext && <div className="country-col-subtext">(gCO₂eq/kWh)</div>}
    </div>
  );
};

export default CarbonIntensitySquare;
