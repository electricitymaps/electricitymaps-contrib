import GlassContainer from 'components/GlassContainer';
import HorizontalDivider from 'components/HorizontalDivider';
import SwitchToggle from 'components/ToggleSwitch';
import { LanguageSelector } from 'features/map-controls/LanguageSelector';
import SpatialAggregatesToggle from 'features/map-controls/SpatialAggregatesToggle';
import { useAtom } from 'jotai';
import { LaptopMinimal, Moon, Sun } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { languageNames } from 'translation/locales';
import { Mode, ThemeOptions } from 'utils/constants';
import {
  colorblindModeAtom,
  productionConsumptionAtom,
  themeAtom,
} from 'utils/state/atoms';

import { isSettingsModalOpenAtom } from './modalAtoms';

function ElectricityFlowsToggle() {
  const { t } = useTranslation();
  const [mode, setMode] = useAtom(productionConsumptionAtom);

  const onToggle = (isEnabled: boolean) => {
    setMode(isEnabled ? Mode.CONSUMPTION : Mode.PRODUCTION);
  };

  return (
    <div className="flex w-full flex-col space-y-1 p-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-secondary dark:text-secondary-dark">
          {t('settings-modal.flows')}
        </span>
        <SwitchToggle
          isEnabled={mode === Mode.CONSUMPTION}
          onChange={onToggle}
          ariaLabel={t('settings-modal.flows')}
        />
      </div>
      <span className="text-xs text-secondary dark:text-secondary-dark">
        {t(
          mode === Mode.CONSUMPTION
            ? 'settings-modal.flow-tracing-enabled'
            : 'settings-modal.flow-tracing-disabled'
        )}
      </span>
    </div>
  );
}

function ThemeToggle({
  theme,
  icon,
  selectedTheme,
  setSelectedTheme,
}: {
  theme: ThemeOptions;
  icon: React.ReactNode;
  selectedTheme: ThemeOptions;
  setSelectedTheme: (theme: ThemeOptions) => void;
}) {
  return (
    <button
      onClick={() => setSelectedTheme(theme)}
      className={`relative flex items-center justify-center p-2.5 ${
        selectedTheme === theme ? 'rounded-2xl bg-neutral-200 dark:bg-neutral-700' : ''
      }`}
    >
      {icon}
    </button>
  );
}

function ThemeToggleGroup() {
  const { t } = useTranslation();
  const [selectedTheme, setSelectedTheme] = useAtom(themeAtom);
  const ICON_SIZE = 20;

  return (
    <div className="flex w-full items-center justify-between p-2">
      <span className="text-sm font-medium text-secondary dark:text-secondary-dark">
        {t('tooltips.changeTheme')}
      </span>
      <div className="flex space-x-1">
        <ThemeToggle
          theme={ThemeOptions.LIGHT}
          icon={<Sun size={ICON_SIZE} />}
          selectedTheme={selectedTheme}
          setSelectedTheme={setSelectedTheme}
        />
        <ThemeToggle
          theme={ThemeOptions.DARK}
          icon={<Moon size={ICON_SIZE} />}
          selectedTheme={selectedTheme}
          setSelectedTheme={setSelectedTheme}
        />
        <ThemeToggle
          theme={ThemeOptions.SYSTEM}
          icon={<LaptopMinimal size={ICON_SIZE} />}
          selectedTheme={selectedTheme}
          setSelectedTheme={setSelectedTheme}
        />
      </div>
    </div>
  );
}

function ColorblindModeToggle() {
  const { t } = useTranslation();
  const [isEnabled, setIsEnabled] = useAtom(colorblindModeAtom);

  const onToggle = (newValue: boolean) => {
    setIsEnabled(newValue);
  };

  return (
    <div className="flex w-full items-center justify-between p-2">
      <span className="text-sm font-medium text-secondary dark:text-secondary-dark">
        {t('legends.colorblindmode')}
      </span>
      <SwitchToggle
        isEnabled={isEnabled}
        onChange={onToggle}
        ariaLabel={t('legends.colorblindmode')}
      />
    </div>
  );
}

function LanguageSelectorToggle() {
  const { t } = useTranslation();
  const { i18n } = useTranslation();
  const currentLanguageKey = i18n.language as keyof typeof languageNames;
  const selectedLanguage = languageNames[currentLanguageKey] ?? 'English';

  const [isOpen, setIsOpen] = useState(false);
  const buttonReference = useRef<HTMLButtonElement>(null);

  const handleToggle = () => setIsOpen(!isOpen);
  const handleClose = () => setIsOpen(false);

  return (
    <div className="w-full p-2">
      <button
        ref={buttonReference}
        className="flex w-full items-center justify-between"
        onClick={handleToggle}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            handleToggle();
          }
        }}
      >
        <span className="text-sm font-medium text-secondary dark:text-secondary-dark">
          {t('Language')}
        </span>
        <span className="text-sm text-secondary dark:text-secondary-dark">
          {selectedLanguage}
        </span>
      </button>
      {isOpen && (
        <LanguageSelector
          isInSettings
          parentRef={buttonReference}
          onClose={handleClose}
        />
      )}
    </div>
  );
}

export function SettingsModalContent() {
  const { t } = useTranslation();
  return (
    <div className="p-2">
      <div className="flex w-full flex-col ">
        <SpatialAggregatesToggle />
        <p className="p-2 text-xs text-secondary dark:text-secondary-dark">
          {t('tooltips.aggregateInfo')}
        </p>
      </div>
      <HorizontalDivider />
      <ElectricityFlowsToggle />
      <HorizontalDivider />
      <LanguageSelectorToggle />
      <HorizontalDivider />
      <ThemeToggleGroup />
      <HorizontalDivider />
      <ColorblindModeToggle />
    </div>
  );
}

export default function SettingsModal() {
  const [isOpen, setIsOpen] = useAtom(isSettingsModalOpenAtom);
  const modalReference = useRef<HTMLDivElement>(null);

  // Handle click outside to close modal
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      // Check if the event target is the settings button
      const isSettingsButton = (event.target as Element)?.closest(
        '[data-testid="settings-button"]'
      );
      // Don't close if clicking the settings button
      if (isSettingsButton) {
        return;
      }
      // Check if the click target is a node and the modal ref exists
      if (
        modalReference.current &&
        event.target instanceof Node && // Type guard for safety
        !modalReference.current.contains(event.target)
      ) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('click', handleClickOutside, true);
    }

    return () => {
      document.removeEventListener('click', handleClickOutside, true);
    };
  }, [isOpen, setIsOpen]);

  if (!isOpen) {
    return null;
  }

  return (
    <div className="absolute right-72 top-3 z-30 mr-14 mt-[env(safe-area-inset-top)]">
      <GlassContainer
        ref={modalReference}
        className="w-72 overflow-hidden rounded-xl shadow-lg"
      >
        <SettingsModalContent />
      </GlassContainer>
    </div>
  );
}
