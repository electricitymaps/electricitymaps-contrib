import React from 'react';

import { useTranslation } from '../../helpers/translation';
import Tooltip from '../tooltip';
import { ZoneName } from './common';

const MapPowerPlantTooltip = ({ powerPlantData, position, onClose }) => {
  const { __ } = useTranslation();
  if (!powerPlantData) {
    return null;
  }

  return (
    <Tooltip id="powerplant-tooltip" position={position} onClose={onClose}>
      <ZoneName zone={powerPlantData.zoneKey} />
      <br />
      {powerPlantData.name}
      <br />
      <br />
      {'Fuel Type'}:
      <br />
      {powerPlantData.fuelType}
      <br />
      <br />
      {'Data Source'}:
      <br />
      {powerPlantData.dataSource}
      <br />
      <br />
      {'Capacity (MW)'}:
      <br />
      {powerPlantData.capacity}
      <br />
    </Tooltip>
  );
};

export default MapPowerPlantTooltip;
