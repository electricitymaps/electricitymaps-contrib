import React from 'react';

import Tooltip from '../tooltip';

const MapPowerPlantTooltip = ({ powerPlantData, position, onClose }) => {
  if (!powerPlantData) {
    return null;
  }

  return (
    <Tooltip id="powerplant-tooltip" position={position} onClose={onClose}>
      {'Power Plant Name'}:
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
      {'Capacity'}:
      <br />
      {powerPlantData.capacity}
      <br />
    </Tooltip>
  );
};

export default MapPowerPlantTooltip;
