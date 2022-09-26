import React, { useEffect, useState, useMemo } from 'react';
import { useSelector } from 'react-redux';
import styled from 'styled-components';

import { dispatchApplication } from '../../store';
import { useRefWidthHeightObserver } from '../../hooks/viewport';

import powerPlants from '../../all_power_plants.json';

import MapPowerPlantTooltip from '../tooltips/mappowerplanttooltip';
import PowerPlant from '../powerplant';

const Layer = styled.div`
  pointer-events: none;
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
`;

const mockPowerPlants = [
    {
       name: "Power Plant 1",
        lonlat: [-2.6240066, 52.1414211],
        fuelType: "coal",
        dataSource: "EIA",
        capacity: 1000,
        zoneKey: "GB",
    }, {
      name: "Power Plant 2",
       lonlat: [12.5937767, 55.6570916],
       fuelType: "gas",
       dataSource: "EIA",
       capacity: 1000,
       zoneKey: "DK-DK2",
   },
];

const getPowerPlants = () => (mockPowerPlants);

export default React.memo(({ project }) => {
  // const powerPlants = getPowerPlants();
  const { ref, width, height } = useRefWidthHeightObserver();

  const isMoving = useSelector((state) => state.application.isMovingMap);
  const [tooltip, setTooltip] = useState(null);

  // Mouse interaction handlers
  const handleArrowMouseMove = useMemo(
    () => (powerPlantData, x, y) => {
      dispatchApplication('isHoveringPowerPlant', true);
      setTooltip({ powerPlantData, position: { x, y } });
    },
    []
  );
  const handleArrowMouseOut = useMemo(
    () => () => {
      dispatchApplication('isHoveringPowerPlant', false);
      setTooltip(null);
    },
    []
  );

  // Call mouse out handler immidiately if moving the map.
  useEffect(
    () => {
      if (isMoving && tooltip) {
        handleArrowMouseOut();
      }
    },
    [isMoving, tooltip] // eslint-disable-line react-hooks/exhaustive-deps
  );

  return (
    <Layer id="powerplants" ref={ref}>
      {tooltip && (
        <MapPowerPlantTooltip
          powerPlantData={tooltip.powerPlantData}
          position={tooltip.position}
          onClose={() => setTooltip(null)}
        />
      )}
      {/* Don't render arrows when moving map - see https://github.com/tmrowco/electricitymap-contrib/issues/1590. */}
      {!isMoving &&
        powerPlants.map((powerPlant) => (
              <PowerPlant
                data={powerPlant}
                key={powerPlant.name}
                mouseMoveHandler={handleArrowMouseMove}
                mouseOutHandler={handleArrowMouseOut}
                project={project}
                viewportWidth={width}
                viewportHeight={height}
              />
            ))}
    </Layer>
  );
});
