import { useColorScale } from 'hooks/theme';
import { useAtom } from 'jotai';
import { memo, type ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import { MapColorSource } from 'utils/constants';
import { mapColorSourceAtom } from 'utils/state/atoms';
import { CarbonUnits } from 'utils/units';

import ColorBar from './ColorBar';

const translationKeys: { [key in MapColorSource]: string } = {
  [MapColorSource.CARBON_INTENSITY]: 'legends.carbonintensity',
  [MapColorSource.RENEWABLE_PERCENTAGE]: 'legends.renewablepercentage',
  [MapColorSource.ELECTRICITY_PRICE]: 'legends.electricityprice',
};
const units: { [key in MapColorSource]: string } = {
  [MapColorSource.CARBON_INTENSITY]: CarbonUnits.GRAMS_CO2EQ_PER_KILOWATT_HOUR,
  [MapColorSource.RENEWABLE_PERCENTAGE]: '%',
  [MapColorSource.ELECTRICITY_PRICE]: '€/MWh',
};

function Legend(): ReactElement {
  const { t } = useTranslation();
  const colorScale = useColorScale();
  const [mapColorSource, setSelectedColorSource] = useAtom(mapColorSourceAtom);

  const handleDropdownChange = (event) => {
    setSelectedColorSource(event.target.value);
  };

  return (
    <div className="text-center">
      <select
        className="font-sm whitespace-nowrap py-1 text-center font-poppins text-sm"
        value={mapColorSource}
        onChange={handleDropdownChange}
      >
        {Object.entries(translationKeys).map(([key, value]) => (
          <option key={key} value={key}>
            {t(value)} ({units[key]})
          </option>
        ))}
      </select>
      <div className="px-2 pt-2">
        <ColorBar colorScale={colorScale} ticksCount={6} id={'legend'} />
      </div>
    </div>
  );
}

export default memo(Legend);
