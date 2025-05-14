import { useColorScale } from 'hooks/theme';
import { useAtom } from 'jotai';
import { memo, type ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import { MapColorSource } from 'utils/constants';
import { mapColorSourceAtom } from 'utils/state/atoms';
import { CarbonUnits } from 'utils/units';

import ColorBar from './ColorBar';
import { LegendItem } from './LegendItem';

function Co2Legend(): ReactElement {
  const { t } = useTranslation();
  const colorScale = useColorScale();
  const [mapColorSource, setSelectedColorSource] = useAtom(mapColorSourceAtom);

  const handleDropdownChange = (event) => {
    setSelectedColorSource(event.target.value);
  };

  let translationKey, unit;
  if (mapColorSource == MapColorSource.CARBON_INTENSITY) {
    translationKey = 'legends.carbonintensity';
    unit = CarbonUnits.GRAMS_CO2EQ_PER_KILOWATT_HOUR;
  } else if (mapColorSource == MapColorSource.RENEWABLE_PERCENTAGE) {
    translationKey = 'legends.renewablepercentage';
    unit = '%';
  } else {
    throw new Error('Invalid map color source');
  }

  return (
    <>
      <label htmlFor="metric-select">Metric:</label>
      <select id="metric-select" value={mapColorSource} onChange={handleDropdownChange}>
        <option value={MapColorSource.CARBON_INTENSITY}>Carbon Intensity</option>
        <option value={MapColorSource.RENEWABLE_PERCENTAGE}>Renewable Percentage</option>
      </select>
      <LegendItem label={t(translationKey)} unit={unit}>
        <ColorBar colorScale={colorScale} ticksCount={6} id={'co2'} />
      </LegendItem>
    </>
  );
}

export default memo(Co2Legend);
