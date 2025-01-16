import { Button } from 'components/Button';
import { Download } from 'lucide-react';
import { useParams } from 'react-router-dom';
import { DEFAULT_ICON_SIZE } from 'utils/constants';

import { getCountryName, getZoneName } from '../../translation/translation';

function getCountryToDownload(zoneId?: string) {
  if (!zoneId) {
    return '';
  }

  const zoneName = getZoneName(zoneId);
  const zoneCountryName =
    zoneId && zoneId.includes('-') && getCountryName(zoneId)?.toLowerCase();
  return zoneCountryName || zoneName;
}

export function DownloadCsv() {
  const { zoneId } = useParams();
  const countryToDownload = getCountryToDownload(zoneId);

  const url = `https://www.electricitymaps.com/data-portal/${countryToDownload.toLowerCase()}?utm_source=app&utm_medium=download_button&utm_campaign=csv_download`;

  return (
    <Button
      href={url}
      icon={<Download size={DEFAULT_ICON_SIZE} />}
      type="tertiary"
      size="md"
      aria-label="Download CSV Data"
    />
  );
}

export default DownloadCsv;
