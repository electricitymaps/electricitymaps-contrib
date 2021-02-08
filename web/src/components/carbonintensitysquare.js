import React from 'react';
import styled from 'styled-components';

import { useCo2ColorScale } from '../hooks/theme';
import { __ } from '../helpers/translation';

const Value = styled.span`
font-weight: bold;
`;

const Box = styled.div`
  background-color: ${props => props.color};
  color: #fff;
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
      <Box
        color={co2ColorScale(value)}
      >
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
