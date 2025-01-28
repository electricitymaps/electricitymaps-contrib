import { Button } from 'components/Button';
import { Download } from 'lucide-react';
import { memo } from 'react';
import { useParams } from 'react-router-dom';
import { DEFAULT_ICON_SIZE } from 'utils/constants';

function DownloadCsv() {
  const { zoneId } = useParams();

  const url = `https://portal.electricitymaps.com/datasets/${zoneId}?utm_source=app&utm_medium=download_button&utm_campaign=csv_download`;

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

export default memo(DownloadCsv);
