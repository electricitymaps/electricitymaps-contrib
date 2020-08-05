import React from 'react';
import getSymbolFromCurrency from 'currency-symbol-map';
import { isNumber } from 'lodash';

import Tooltip from '../tooltip';

const PriceTooltip = ({ position, zoneData, onClose }) => {
  if (!zoneData) return null;

  const priceIsDefined = zoneData.price && isNumber(zoneData.price.value);
  const currency = priceIsDefined ? getSymbolFromCurrency(zoneData.price.currency) : '?';
  const value = priceIsDefined ? zoneData.price.value : '?';

  return (
    <Tooltip id="price-tooltip" position={position} onClose={onClose}>
      {value} {currency} / MWh
    </Tooltip>
  );
};

export default PriceTooltip;
