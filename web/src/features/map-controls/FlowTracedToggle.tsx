import { useAtom } from 'jotai';
import { ChevronsUp } from 'lucide-react';
import { memo, type ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import trackEvent from 'utils/analytics';
import { Mode, TrackEvent } from 'utils/constants';
import { productionConsumptionAtom } from 'utils/state/atoms';

import MapButton from './MapButton';

function FlowTracedToggle(): ReactElement {
  const { t } = useTranslation();
  const [currentMode, setCurrentMode] = useAtom(productionConsumptionAtom);
  const isConsumption = currentMode === Mode.CONSUMPTION;

  const handleToggle = () => {
    const newMode = isConsumption ? Mode.PRODUCTION : Mode.CONSUMPTION;

    trackEvent(TrackEvent.PRODUCTION_CONSUMPTION_CLICKED, {
      productionConsumption: newMode,
    });

    setCurrentMode(newMode);
  };

  return (
    <MapButton
      icon={<ChevronsUp size={20} className={isConsumption ? '' : 'opacity-50'} />}
      tooltipText={isConsumption ? t('tooltips.flowTraced') : t('tooltips.nonFlowTraced')}
      dataTestId="flow-traced-toggle-button"
      onClick={handleToggle}
      asToggle
    />
  );
}

export default memo(FlowTracedToggle);
