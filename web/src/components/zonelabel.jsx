import React from 'react';
import styled from 'styled-components';
import Tooltip from './tooltip';
import { useTranslation } from '../helpers/translation';
import { noop } from '../helpers/noop';

const LABEL_TYPES = {
  ESTIMATED: {
    styling: {
      background: '#ffd700',
      color: '#000',
    },
    id: 'estimated',
    translationId: 'country-panel.estimated',
    tooltipTranslationId: 'country-panel.estimatedTooltip',
  },
  AGGREGATED: {
    styling: {
      background: '#c9c9c9',
      color: '#000',
    },
    id: 'aggregated',
    translationId: 'country-panel.aggregated',
    tooltipTranslationId: 'country-panel.aggregatedTooltip',
  },
};

const Label = styled.div`
  display: inline-block;
  padding: 0 4px;
  margin-left: 4px;
  border-radius: 4px;
  max-height: 20px;
  ${(props) => props.type.styling}
  &:hover {
    cursor: help;
  }
`;

const TooltipInner = styled.div`
  max-width: 180px;
  font-size: smaller;
`;

const ZoneLabel = ({ isMobile, type }) => {
  const [tooltip, setTooltip] = React.useState(null);
  const { __ } = useTranslation();

  const TooltipComponent = tooltip && (
    <Tooltip id={`${type.id}-info-tooltip`} position={{ x: tooltip.clientX, y: tooltip.clientY }}>
      <TooltipInner>{__(type.tooltipTranslationId)}</TooltipInner>
    </Tooltip>
  );

  return (
    <React.Fragment>
      <Label
        type={type}
        onClick={isMobile ? ({ clientX, clientY }) => setTooltip({ clientX, clientY }) : noop}
        onMouseMove={!isMobile ? ({ clientX, clientY }) => setTooltip({ clientX, clientY }) : noop}
        onMouseOut={() => setTooltip(null)}
        onBlur={() => setTooltip(null)}
      >
        {__(type.translationId)}
      </Label>
      {TooltipComponent}
    </React.Fragment>
  );
};

export { ZoneLabel, LABEL_TYPES };
