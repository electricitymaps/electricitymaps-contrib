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
  ${(props) => (props as any).type.styling}
  &:hover {
    cursor: help;
  }
`;

const TooltipInner = styled.div`
  max-width: 180px;
  font-size: smaller;
`;

const ZoneLabel = ({ isMobile, type }: any) => {
  const [tooltip, setTooltip] = React.useState(null);
  const { __ } = useTranslation();

  const TooltipComponent = tooltip && (
    <Tooltip id={`${type.id}-info-tooltip`} position={{ x: (tooltip as any).clientX, y: (tooltip as any).clientY }}>
      <TooltipInner>{__(type.tooltipTranslationId)}</TooltipInner>
    </Tooltip>
  );

  return (
    <React.Fragment>
      <Label
        // @ts-expect-error TS(2769): No overload matches this call.
        type={type}
        // @ts-expect-error TS(2345): Argument of type '{ clientX: number; clientY: numb... Remove this comment to see the full error message
        onClick={isMobile ? ({ clientX, clientY }) => setTooltip({ clientX, clientY }) : noop}
        // @ts-expect-error TS(2345): Argument of type '{ clientX: number; clientY: numb... Remove this comment to see the full error message
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
