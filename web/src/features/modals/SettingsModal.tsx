import * as Dialog from '@radix-ui/react-dialog';
import Accordion from 'components/Accordion';
import GlassContainer from 'components/GlassContainer';
import HorizontalDivider from 'components/HorizontalDivider';
import Link from 'components/Link';
import SwitchToggle from 'components/ToggleSwitch';
import { LanguageSelector } from 'features/map-controls/LanguageSelector';
import SpatialAggregatesToggle from 'features/map-controls/SpatialAggregatesToggle';
import { useAtom } from 'jotai';
import {
  LaptopMinimalIcon,
  MoonIcon,
  SmartphoneIcon,
  SunIcon,
  XIcon,
} from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { languageNames } from 'translation/locales';
import { Mode, ThemeOptions } from 'utils/constants';
import {
  colorblindModeAtom,
  productionConsumptionAtom,
  themeAtom,
} from 'utils/state/atoms';
import { useIsMobile } from 'utils/styling';

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
  const isMobile = useIsMobile();

  return (
    <div className="flex w-full items-center justify-between p-2">
      <span className="text-sm font-medium text-secondary dark:text-secondary-dark">
        {t('tooltips.changeTheme')}
      </span>
      <div className="flex space-x-1">
        <ThemeToggle
          theme={ThemeOptions.LIGHT}
          icon={<SunIcon size={ICON_SIZE} />}
          selectedTheme={selectedTheme}
          setSelectedTheme={setSelectedTheme}
        />
        <ThemeToggle
          theme={ThemeOptions.DARK}
          icon={<MoonIcon size={ICON_SIZE} />}
          selectedTheme={selectedTheme}
          setSelectedTheme={setSelectedTheme}
        />
        <ThemeToggle
          theme={ThemeOptions.SYSTEM}
          icon={
            isMobile ? (
              <SmartphoneIcon size={ICON_SIZE} />
            ) : (
              <LaptopMinimalIcon size={ICON_SIZE} />
            )
          }
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
  const { t, i18n } = useTranslation();
  const currentLanguageKey = i18n.languages[0] as keyof typeof languageNames;
  const selectedLanguage = languageNames[currentLanguageKey] ?? 'English';

  const [isOpen, setIsOpen] = useState(false);
  const buttonReference = useRef<HTMLButtonElement>(null);

  const handleToggle = useCallback(() => setIsOpen(!isOpen), [isOpen]);
  const handleClose = useCallback(() => setIsOpen(false), []);
  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.key === 'Enter' || event.key === ' ') {
        handleToggle();
      }
    },
    [handleToggle]
  );

  return (
    <div className="w-full p-2">
      <button
        ref={buttonReference}
        className="flex w-full items-center justify-between"
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
      >
        <span className="text-sm font-medium text-secondary dark:text-secondary-dark">
          {t('Language')}
        </span>
        <span className="text-sm text-secondary dark:text-secondary-dark">
          {selectedLanguage}
        </span>
      </button>
      {isOpen && <LanguageSelector parentRef={buttonReference} onClose={handleClose} />}
    </div>
  );
}

function AboutElectricityMaps() {
  const { t } = useTranslation();
  const [isCollapsed, setIsCollapsed] = useState(true);

  return (
    <div className="w-full px-2 pt-2">
      <Accordion
        title={
          <p className="text-secondary dark:text-secondary-dark">{t('info.title')}</p>
        }
        isCollapsed={isCollapsed}
        setState={setIsCollapsed}
      >
        <div className="mt-2 text-xs text-secondary dark:text-secondary-dark">
          <p className="mb-4">
            <Link href="https://electricitymaps.com">Electricity Maps</Link> offers an API
            that delivers real-time and predictive electricity grid signals.
          </p>

          <div className="mb-2">
            <Link isExternal href="https://electricitymaps.com/privacy-policy">
              {t('button.privacy-policy')}
            </Link>
          </div>

          <div className="mb-4">
            <Link isExternal href="https://electricitymaps.com/legal-notice">
              {t('button.legal-notice')}
            </Link>
          </div>

          <p className="pb-2 text-xs text-secondary dark:text-secondary-dark">
            {t('info.version', { version: APP_VERSION })}
          </p>
        </div>
      </Accordion>
    </div>
  );
}

export function SettingsModalContent() {
  const { t } = useTranslation();
  return (
    <div className="max-h-[80vh] overflow-y-auto px-3 py-4">
      <div className="flex w-full flex-col">
        <SpatialAggregatesToggle />
        <p className="p-2 text-xs text-secondary dark:text-secondary-dark">
          {t('tooltips.aggregateInfo')}
        </p>
      </div>
      <HorizontalDivider />
      <ElectricityFlowsToggle />
      <HorizontalDivider />
      <LanguageSelectorToggle />
      <ThemeToggleGroup />
      <HorizontalDivider />
      <ColorblindModeToggle />
      <HorizontalDivider />
      <AboutElectricityMaps />
    </div>
  );
}

function MobileDismissButton({
  onClick,
  style,
}: {
  onClick: () => void;
  style?: React.CSSProperties;
}) {
  const { t } = useTranslation();
  return (
    <div
      className="absolute inset-x-0 mx-auto flex justify-center md:hidden"
      style={style}
    >
      <GlassContainer className="flex h-9 w-9 items-center justify-center rounded-full ">
        <button aria-label={t('misc.dismiss')} onClick={onClick}>
          <XIcon size={20} />
        </button>
      </GlassContainer>
    </div>
  );
}

export default function SettingsModal() {
  const [isOpen, setIsOpen] = useAtom(isSettingsModalOpenAtom);
  const modalReference = useRef<HTMLDivElement>(null);
  const [modalHeight, setModalHeight] = useState(428);
  const { t } = useTranslation();

  const handleClose = () => {
    setIsOpen(false);
  };

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const modalElement = modalReference.current;
    if (!modalElement) {
      return;
    }

    const updateModalHeight = () => {
      if (modalElement) {
        const height = modalElement.getBoundingClientRect().height;
        setModalHeight(height + 23); // 3px top offset + 20px for safe spacing
      }
    };

    // Initial height calculation
    updateModalHeight();

    // Update height on resize
    const resizeObserver = new ResizeObserver(updateModalHeight);
    resizeObserver.observe(modalElement);

    // Detect content changes that might affect height but not trigger resize events
    const mutationObserver = new MutationObserver(updateModalHeight);
    mutationObserver.observe(modalElement, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true,
    });

    return () => {
      if (modalElement) {
        resizeObserver.unobserve(modalElement);
        mutationObserver.disconnect();
      }
    };
  }, [isOpen]);

  // Skip if modal isn't open
  if (!isOpen) {
    return null;
  }

  return (
    <Dialog.Root open={isOpen} onOpenChange={setIsOpen}>
      <Dialog.Portal>
        {/* Semi-transparent overlay */}
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50 md:bg-transparent" />

        {/* Modal content */}
        <Dialog.Content
          onOpenAutoFocus={(event: Event) => event.preventDefault()}
          className="pointer-events-auto fixed inset-0 z-[51] overflow-auto"
          onClick={(event_) => {
            // Close when clicking directly on the content area (not its children)
            if (event_.target === event_.currentTarget) {
              handleClose();
            }
          }}
        >
          <div className="pointer-events-auto absolute inset-x-0 top-3 mt-[env(safe-area-inset-top)] flex justify-center md:inset-x-auto md:right-72 md:mr-14 md:justify-start">
            <GlassContainer
              ref={modalReference}
              className="w-full max-w-xs rounded-xl shadow-lg md:w-72"
            >
              <SettingsModalContent />
            </GlassContainer>
          </div>

          <div className="pointer-events-auto">
            <MobileDismissButton
              onClick={handleClose}
              style={{ top: `${modalHeight}px` }}
            />
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
