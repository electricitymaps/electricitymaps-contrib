import React from 'react';
import getSymbolFromCurrency from 'currency-symbol-map';

import Tooltip from '../tooltip';

const PriceTooltip = ({ position, zoneData, onClose }) => {
  if (!zoneData) {
    return null;
  }

  const priceIsDefined = zoneData.price && typeof zoneData.price.value === 'number';
  const currency = priceIsDefined ? getSymbolFromCurrency(zoneData.price.currency) : '?';
  const value = priceIsDefined ? zoneData.price.value : '?';

  return (
    <Tooltip id="price-tooltip" position={position} onClose={onClose}>
      {value} {currency} / MWh
    </Tooltip>
  );
};

export default PriceTooltip;
