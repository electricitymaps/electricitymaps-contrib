import { SourceColorAnnouncementImage } from 'icons/announcementSourceColorImage';
import { useAtom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { HiXMark } from 'react-icons/hi2';
import { hasOnboardingBeenSeenAtom } from 'utils/state/atoms';

const hasAnnouncementBeenSeenAtom = atomWithStorage(
  'announcementSeen',
  localStorage.getItem('announcementSeen') ?? false
);

const handleTierGaterClick = (event: React.MouseEvent<HTMLDivElement>) => {
  event.stopPropagation();
  event.preventDefault();
};

export default function AnnouncementModal() {
  const { t } = useTranslation();
  const [hasAnnouncementBeenSeen, setHasAnnouncementBeenSeen] = useAtom(
    hasAnnouncementBeenSeenAtom
  );
  const [hasOnboardingBeenSeen] = useAtom(hasOnboardingBeenSeenAtom);
  const [hasOnboardingBeenSeenInSession, setHasOnboardingBeenSeenInSession] =
    useState(false);
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

  if (
    hasAnnouncementBeenSeen ||
    isExpired ||
    !hasOnboardingBeenSeen ||
    hasOnboardingBeenSeenInSession
  ) {
    return null;
  }

  return (
    <div
      role="presentation"
      onClick={handleDismiss}
      onKeyDown={handleDismiss}
      className="absolute left-0 top-0 z-50 flex h-full w-full flex-col items-center justify-center bg-black/20"
    >
      <div
        role="presentation"
        onClick={handleTierGaterClick}
        className="z-50 max-w-[361px] overflow-hidden rounded-3xl border border-neutral-200 dark:border-gray-700"
      >
        <SourceColorAnnouncementImage />
        <div className="h-40 bg-zinc-50 opacity-95 dark:bg-gray-900">
          <div className="text-wrap px-10 pt-3 text-center text-lg font-medium">
            {t('announcement-modal.title')}
          </div>
          <div className="text-wrap px-10 pt-2 text-center text-base">
            {t('announcement-modal.content')}
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
