import useGetState from 'api/getState';
import ZoneGaugesWithCO2Square from 'components/ZoneGauges';
import { useAtomValue } from 'jotai';
import { selectedDatetimeStringAtom } from 'utils/state/atoms';

export function ZoneHeaderGauges({ zoneKey }: { zoneKey?: string }) {
  const { data } = useGetState();
  const selectedDatetimeString = useAtomValue(selectedDatetimeStringAtom);
  if (!data || !zoneKey) {
    return null;
  }
  const selectedData = data.datetimes[selectedDatetimeString]?.z[zoneKey];

  return <ZoneGaugesWithCO2Square zoneData={selectedData} withTooltips />;
}
