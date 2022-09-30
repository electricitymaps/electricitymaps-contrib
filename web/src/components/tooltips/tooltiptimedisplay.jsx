/* eslint-disable*/
import React from 'react';
import styled from 'styled-components';
import { TimeDisplay } from '../timeDisplay';

const StyledTimeDisplay = styled(TimeDisplay)`
  font-size: smaller;
  margin-top: 0px;
  font-weight: 600;
`;

function TooltipTimeDisplay({ className, date }) {
  return <StyledTimeDisplay className={className} date={date} />;
}

export default TooltipTimeDisplay;
