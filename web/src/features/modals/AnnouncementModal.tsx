import { Link } from 'components/Link';
import { SourceColorAnnouncementImage } from 'icons/announcementSourceColorImage';
import { useAtom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';
import { useEffect, useState } from 'react';
import { HiXMark } from 'react-icons/hi2';
import { useSearchParams } from 'react-router-dom';
import { hasOnboardingBeenSeenAtom } from 'utils/state/atoms';

const hasAnnouncementBeenSeenAtom = atomWithStorage(
  'announcementSeen',
  localStorage.getItem('announcementSeen') ?? false
);

export default function AnnouncementModal() {
  const [hasAnnouncementBeenSeen, setHasAnnouncementBeenSeen] = useAtom(
    hasAnnouncementBeenSeenAtom
  );
  const [hasOnboardingBeenSeen] = useAtom(hasOnboardingBeenSeenAtom);
  const [hasOnboardingBeenSeenInSession, setHasOnboardingBeenSeenInSession] =
    useState(false);
  const [searchParameters] = useSearchParams();
  const skipOnboarding = searchParameters.get('skip-onboarding') === 'true';
  const isExpired = new Date() > new Date('2024-07-15');

  // Check if onboarding has been seen in the current session
  useEffect(() => {
    const onboardingSeenInSession = sessionStorage.getItem('onboardingSeenInSession');
    if (onboardingSeenInSession) {
      setHasOnboardingBeenSeenInSession(true);
    } else if (!hasOnboardingBeenSeen) {
      sessionStorage.setItem('onboardingSeenInSession', 'true');
      setHasOnboardingBeenSeenInSession(true);
    }
  }, [hasOnboardingBeenSeen]);

  const handleDismiss = () => {
    setHasAnnouncementBeenSeen(true);
  };

  const handleClick = (event: React.MouseEvent<HTMLDivElement>) => {
    const target = event.target as HTMLElement;

    if (target.id === 'backdrop') {
      handleDismiss();
    }
    return;
  };

  if (
    hasAnnouncementBeenSeen ||
    isExpired ||
    skipOnboarding ||
    !hasOnboardingBeenSeen ||
    hasOnboardingBeenSeenInSession
  ) {
    return null;
  }

  return (
    <div
      role="presentation"
      className="absolute left-0 top-0 z-30 flex h-full w-full flex-col items-center justify-center bg-black/20"
      onClick={handleClick}
      id="backdrop"
    >
      <div
        role="presentation"
        className="z-50 max-w-[361px] overflow-hidden rounded-3xl border border-neutral-200 dark:border-gray-700"
      >
        <SourceColorAnnouncementImage />
        <div className="h-56 bg-zinc-50 opacity-95 dark:bg-gray-900">
          <div className="text-wrap px-10 pt-3 text-center text-lg font-medium">
            {'Introducing a visual update to our app!'}
          </div>
          <div className="text-wrap px-10 pt-2 text-center text-base">
            {
              "We've renewed the colors representing electricity sources to align with industry standards and introduced a new ordering and sorting system."
            }
          </div>
          <div className="pointer-events-auto pt-3 text-center">
            <Link href="https://electricitymaps.notion.site/2024-06-New-production-mode-colors-and-order-5daedf4ece634da891f5f533a7977aea">
              Read more about this change
            </Link>
          </div>
        </div>
      </div>
      <button
        onClick={handleDismiss}
        className="p-auto pointer-events-auto mt-2 flex h-10 w-10 items-center justify-center self-center rounded-full border border-neutral-200 bg-zinc-50 text-black shadow-md dark:border-gray-700 dark:bg-gray-900 dark:text-white"
      >
        <HiXMark size="24" />
      </button>
    </div>
  );
}
