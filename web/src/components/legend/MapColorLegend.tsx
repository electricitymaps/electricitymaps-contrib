import { useColorScale } from 'hooks/theme';
import { useAtom } from 'jotai';
import { memo, type ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import {
  MapColorSource,
  mapColorSourceTranslationKeys,
  unitsByMapColorSource,
} from 'utils/constants';
import { mapColorSourceAtom } from 'utils/state/atoms';

import ColorBar from './ColorBar';

function Legend(): ReactElement {
  const { t } = useTranslation();
  const colorScale = useColorScale();
  const [mapColorSource, setSelectedColorSource] = useAtom(mapColorSourceAtom);

  const handleDropdownChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedColorSource(event.target.value as MapColorSource);
  };

  return (
    <div className="text-center">
      <select
        className="font-sm whitespace-nowrap py-1 text-center font-poppins text-sm"
        value={mapColorSource}
        onChange={handleDropdownChange}
      >
        {Object.entries(mapColorSourceTranslationKeys).map(([key, value]) => (
          <option key={key} value={key}>
            {t(value)} ({unitsByMapColorSource[key as keyof typeof unitsByMapColorSource]}
            )
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
