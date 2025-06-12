import { useAtom } from 'jotai';
import { ArrowLeft } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useLocation } from 'react-router-dom';
import { formatDate } from 'utils/formatting';
import { useNavigateWithParameters } from 'utils/helpers';

import { TimeRange } from '../../../utils/constants';
import { getStatusColor } from '../../assets/utils';
import { selectedSolarAssetAtom } from '../../map/mapAtoms';
import GenericPanel from '../InterfacePanel';

export default function SolarAssetPanel() {
  const [selectedAsset, setSelectedAsset] = useAtom(selectedSolarAssetAtom);
  const navigate = useNavigateWithParameters();
  const location = useLocation();
  const { i18n } = useTranslation();

  if (!selectedAsset) {
    return null;
  }

  const { properties } = selectedAsset;

  const handleClose = () => {
    setSelectedAsset(null);
    // Check if we are on a path that implies an asset is selected in the URL structure.
    // This logic might need adjustment depending on final routing for assets.
    const isAssetPath = location.pathname.includes('/solar-asset');

    if (isAssetPath) {
      // Navigate to the base map view, preserving current map parameters if possible
      // This part is a simplified navigation, assuming we want to go back to /map
      // and that navigate hook handles existing params like timeRange, resolution.
      navigate({ to: '/map', keepHashParameters: true });
    }
  };

  const name =
    String(properties.name) || String(properties.ASSET_NAME) || 'Unnamed Asset';
  const capacityMw = Number.parseFloat(String(properties.capacity_mw));
  const source = properties.source ? String(properties.source) : null;
  const maybeUrl = properties.url ? String(properties.url) : null;

  let sourceUrl = new URL(
    'https://www.globalenergymonitor.org/projects/global-solar-power-tracker/'
  );
  if (maybeUrl) {
    try {
      sourceUrl = new URL(maybeUrl);
    } catch (error) {
      console.error('[SolarAssetPanel] Invalid URL:', maybeUrl, error);
    }
  } else if (source) {
    try {
      sourceUrl = new URL(source); // This will throw if the URL is invalid
    } catch (error) {
      console.error('[SolarAssetPanel] Invalid URL:', source, error);
    }
  }

  const commissionYear = properties.commission_year
    ? String(Math.floor(Number(properties.commission_year)))
    : null;

  const date = new Date(String(properties.capacity_update_date));

  const capacityUpdateDate = formatDate(date, i18n.languages[0], TimeRange.M3);
  let status = properties.status ? String(properties.status) : 'Unknown';
  let isCommissionedInPast = false;

  if (commissionYear) {
    const numericCommissionYear = Number.parseInt(commissionYear, 10);
    const currentYear = new Date().getFullYear();
    if (!Number.isNaN(numericCommissionYear) && numericCommissionYear <= currentYear) {
      isCommissionedInPast = true;
      if (status.toLowerCase() === 'unknown') {
        status = 'Operational';
      }
    }
  }

  const backButton = (
    <button
      onClick={handleClose}
      className="self-center p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
      aria-label="Back to map"
      data-testid="solar-asset-data-box-back-button"
    >
      <ArrowLeft className="h-5 w-5" />
    </button>
  );

  return (
    <GenericPanel
      title={name}
      iconSrc="/images/solar_asset.png"
      customHeaderStartContent={backButton}
      contentClassName="p-3 md:p-4"
    >
      {/* Content for the solar asset details */}
      <div className="space-y-3 text-sm text-gray-700 dark:text-gray-300">
        {!Number.isNaN(capacityMw) && (
          <div className="flex justify-between font-medium">
            <span>Capacity:</span>
            <span className="text-gray-900 dark:text-gray-100">
              {`${capacityMw.toFixed(1)} MW`}
            </span>
          </div>
        )}
        <div className="flex items-center justify-between">
          <span>Status:</span>
          <div className="flex items-center">
            <span
              className={`mr-1.5 h-2.5 w-2.5 rounded-full ${getStatusColor(status)}`}
              aria-hidden="true"
            />
            <span className="font-medium text-gray-900 dark:text-gray-100">{status}</span>
          </div>
        </div>
        {commissionYear && (
          <div className="flex justify-between">
            <span>
              {isCommissionedInPast ? 'Operational since:' : 'Commission Year:'}
            </span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {commissionYear}
            </span>
          </div>
        )}
        {capacityUpdateDate && capacityUpdateDate !== 'N/A' && (
          <div className="flex justify-between">
            <span>Capacity Data Updated:</span>
            <time
              dateTime={date.toISOString()}
              className="font-medium text-gray-900 dark:text-gray-100"
            >
              {capacityUpdateDate}
            </time>
          </div>
        )}

        <div className="border-t border-gray-200 pt-2 dark:border-gray-700" />

        <div>
          <span className="mr-1 font-semibold">Source:</span>
          <span className="text-gray-900 dark:text-gray-100">
            Global Solar Power Tracker, Global Energy Monitor and TransitionZero, February
            2025 release.
            {sourceUrl && (
              <>
                <br />
                <a
                  href={sourceUrl.toString()}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline dark:text-blue-400"
                >
                  Learn more at Global Energy Monitor.
                </a>
              </>
            )}
          </span>
        </div>
      </div>
    </GenericPanel>
  );
}
