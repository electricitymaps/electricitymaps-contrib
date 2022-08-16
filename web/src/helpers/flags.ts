// @ts-expect-error TS(2732): Cannot find module '../../../config/zones.json'. C... Remove this comment to see the full error message
import zones from '../../../config/zones.json';
import { DEFAULT_FLAG_SIZE } from '../helpers/constants';

const flagUri = function (countryCode: any, flagSize = DEFAULT_FLAG_SIZE) {
  if (!countryCode) {
    return undefined;
  }
  const zoneFlagFile = (zones[countryCode.toUpperCase()] || {}).flag_file_name;
  const flagFile = zoneFlagFile || `${countryCode.toLowerCase().split('-')[0]}.png`;
  // @ts-expect-error TS(2304): Cannot find name 'resolvePath'.
  return resolvePath(`images/flag-icons/flags_iso/${flagSize}/${flagFile}`);
};

export { flagUri };
