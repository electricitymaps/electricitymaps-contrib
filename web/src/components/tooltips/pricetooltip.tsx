import React from 'react';
// @ts-expect-error TS(7016): Could not find a declaration file for module 'curr... Remove this comment to see the full error message
import getSymbolFromCurrency from 'currency-symbol-map';

import Tooltip from '../tooltip';
import TooltipTimeDisplay from './tooltiptimedisplay';

const PriceTooltip = ({ position, zoneData, onClose }: any) => {
  if (!zoneData) {
    return null;
  }

  const priceIsDefined = zoneData.price && typeof zoneData.price.value === 'number';
  const currency = priceIsDefined ? getSymbolFromCurrency(zoneData.price.currency) : '?';
  const value = priceIsDefined ? zoneData.price.value : '?';

  return (
    <Tooltip id="price-tooltip" position={position} onClose={onClose}>
      <TooltipTimeDisplay date={zoneData.stateDatetime} />
      {value} {currency} / MWh
    </Tooltip>
  );
};

export default PriceTooltip;
