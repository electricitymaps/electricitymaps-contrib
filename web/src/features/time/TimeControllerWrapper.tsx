import GlassContainer from 'components/GlassContainer';
import { useDropdownCtl } from 'components/MoreOptionsDropdown';
import { loadingMapAtom } from 'features/map/mapAtoms';
import { useAtomValue } from 'jotai';
import { BottomSheet } from 'react-spring-bottom-sheet';
import { hasOnboardingBeenSeenAtom, isHourlyAtom } from 'utils/state/atoms';
import { useBreakpoint } from 'utils/styling';

import HistoricalTimeHeader from './HistoricalTimeHeader';
import TimeController from './TimeController';

function useHistoricalTimeHeader(): {
  shouldShowHistoricalNavigator: boolean;
  onToggleDropdown: () => void;
  onDismiss: () => void;
} {
  const isHourly = useAtomValue(isHourlyAtom);
  const { isOpen, onToggleDropdown, onDismiss } = useDropdownCtl();
  const shouldShowHistoricalNavigator = isHourly && isOpen;

  return { shouldShowHistoricalNavigator, onToggleDropdown, onDismiss };
}

function BottomSheetWrappedTimeController() {
  const isLoadingMap = useAtomValue(loadingMapAtom);
  const hasOnboardingBeenSeen = useAtomValue(hasOnboardingBeenSeenAtom);
  const safeAreaBottomString = getComputedStyle(
    document.documentElement
  ).getPropertyValue('--sab');
  const { shouldShowHistoricalNavigator, onToggleDropdown, onDismiss } =
    useHistoricalTimeHeader();

  const safeAreaBottom = safeAreaBottomString
    ? Number.parseInt(safeAreaBottomString.replace('px', ''))
    : 0;
  const SNAP_POINTS = [60 + safeAreaBottom, 125 + safeAreaBottom];

  // Don't show the time controller until the onboarding has been seen
  // But it still has to be rendered to avoid re-querying data and showing loading
  // indicators again. Therefore we set the snap points to 0 until modal is closed.
  const snapPoints = hasOnboardingBeenSeen && !isLoadingMap ? SNAP_POINTS : [0, 0];

  return (
    <BottomSheet
      scrollLocking={false} // Ensures scrolling is not blocked on IOS
      open={!isLoadingMap}
      snapPoints={() => snapPoints}
      blocking={false}
    >
      {shouldShowHistoricalNavigator && (
        <div className="absolute z-[20] w-full -translate-y-14 px-2">
          <HistoricalTimeHeader onClose={onDismiss} floating />
        </div>
      )}
      <TimeController className="p-0.5 min-[370px]:px-4" onToggle={onToggleDropdown} />
    </BottomSheet>
  );
}

function FloatingTimeController() {
  const { shouldShowHistoricalNavigator, onToggleDropdown, onDismiss } =
    useHistoricalTimeHeader();

  return (
    <GlassContainer className="pointer-events-auto absolute bottom-3 left-3 flex w-full flex-col px-4 py-3">
      {shouldShowHistoricalNavigator && (
        <div className="border-1 z-[22] mb-1 border-b border-neutral-200 px-0.5 pb-2 dark:border-neutral-700">
          <HistoricalTimeHeader onClose={onDismiss} />
        </div>
      )}
      <TimeController onToggle={onToggleDropdown} />
    </GlassContainer>
  );
}

export default function TimeControllerWrapper() {
  const isBiggerThanMobile = useBreakpoint('sm');
  return isBiggerThanMobile ? (
    <FloatingTimeController />
  ) : (
    <BottomSheetWrappedTimeController />
  );
}
