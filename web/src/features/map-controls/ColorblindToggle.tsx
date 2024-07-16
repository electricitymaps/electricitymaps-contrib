import { Button } from 'components/Button';
import { useAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { HiOutlineEyeOff } from 'react-icons/hi';
import trackEvent from 'utils/analytics';
import { colorblindModeAtom } from 'utils/state/atoms';

export default function ColorblindToggle() {
  const { t } = useTranslation();
  const [isColorblindModeEnabled, setIsColorblindModeEnabled] =
    useAtom(colorblindModeAtom);

  const handleColorblindModeToggle = () => {
    setIsColorblindModeEnabled(!isColorblindModeEnabled);
    trackEvent('Colorblind Mode Toggled');
  };

  return (
    <Button
      size="md"
      type="opaque"
      icon={
        <HiOutlineEyeOff
          size={20}
          className={`${isColorblindModeEnabled ? '' : 'opacity-50'}`}
        />
      }
      dataTestId="colorblind-layer-button"
      tooltipText={t('legends.colorblindmode')}
      onClick={handleColorblindModeToggle}
      ariaLabel={t('aria.label.colorBlindMode')}
    />
  );
}
