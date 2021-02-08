import React from 'react';
import styled from 'styled-components';

import { useCo2ColorScale } from '../hooks/theme';
import { __ } from '../helpers/translation';

/**
 * This function finds the optimal text color based on YIQ contrast.
 * Based on https://medium.com/@druchtie/contrast-calculator-with-yiq-5be69e55535c
 * @param {string} rgbColor a string with the background color (e.g. "rgb(0,5,4)")
 */
const getTextColor = (rgbColor) => {
  const colors = rgbColor.replace(/[^\d,.]/g, '').split(',');
  const r = parseInt(colors[0], 10);
  const g = parseInt(colors[1], 10);
  const b = parseInt(colors[2], 10);
  const contrastRatio = (r * 299 + g * 587 + b * 114) / 1000;
  return contrastRatio > 128 ? 'black' : 'white';
};

const Value = styled.span`
  font-weight: bold;
`;

const Box = styled.div`
  background-color: ${props => props.color};
  color: ${props => getTextColor(props.color)};
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
