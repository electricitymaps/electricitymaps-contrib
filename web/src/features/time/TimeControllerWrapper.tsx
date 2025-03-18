import GlassContainer from 'components/GlassContainer';
import { useFeatureFlag } from 'features/feature-flags/api';
import { loadingMapAtom } from 'features/map/mapAtoms';
import { useAtomValue } from 'jotai';
import { BottomSheet } from 'react-spring-bottom-sheet';
import { hasOnboardingBeenSeenAtom } from 'utils/state/atoms';
import { useBreakpoint } from 'utils/styling';

import HistoricalTimeHeader from './HistoricalTimeHeader';
import TimeController from './TimeController';
import TimeHeader from './TimeHeader';

function BottomSheetWrappedTimeController() {
  const isLoadingMap = useAtomValue(loadingMapAtom);
  const hasOnboardingBeenSeen = useAtomValue(hasOnboardingBeenSeenAtom);
  const safeAreaBottomString = getComputedStyle(
    document.documentElement
  ).getPropertyValue('--sab');
  const historicalLinkingEnabled = useFeatureFlag('historical-linking');

  const safeAreaBottom = safeAreaBottomString
    ? Number.parseInt(safeAreaBottomString.replace('px', ''))
    : 0;
  const SNAP_POINTS = [60 + safeAreaBottom, 170 + safeAreaBottom];

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
      header={historicalLinkingEnabled ? <HistoricalTimeHeader /> : <TimeHeader />}
    >
      <TimeController className="p-2 min-[370px]:px-4" />
    </BottomSheet>
  );
}

function FloatingTimeController() {
  return (
    <GlassContainer className="pointer-events-auto bottom-3 left-3 px-4 py-3">
      <TimeController />
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
