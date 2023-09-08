import {
  hasOnboardingBeenSeenAtom,
  hasTotalEnergyIntroBeenSeenAtom,
} from 'utils/state/atoms';

import Modal from 'components/Modal';
import { useAtom } from 'jotai';
import { resolvePath, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'translation/translation';

export function InfoModalContent() {
  const { __ } = useTranslation();
  const image = resolvePath('images/onboarding/totalEnergyIntro.png').pathname;
  return (
    <>
      <div
        className={`block h-72 w-full rounded-t-xl bg-auto bg-top bg-no-repeat`}
        style={{
          backgroundImage: `url("${image}")`,
          backgroundSize: `cover`,
        }}
      ></div>
      <div className="flex w-auto flex-col justify-center px-4 pb-6 pt-2 text-center dark:bg-gray-700">
        <p className="pb-2 pt-2 font-poppins text-sm text-gray-500 dark:text-gray-400">
          Important Update &mdash; September 2023
        </p>
        <h2 className="mb-2 text-base sm:text-xl">
          Now showing total electricity usage over time!
        </h2>
        <div className="px-12 text-sm sm:text-base">
          <p className="mb-4">
            Instead of showing average numbers for the daily, monthly and yearly periods,
            the app now displays the <strong>total amount of electricity</strong>{' '}
            consumed/produced for the selected time period.
          </p>
          <p className="mb-6">
            We believe this makes it easier to compare the numbers and understand how
            electricity usage changes over time.
          </p>
          <p className="text-gray-500 dark:text-gray-400">
            Got questions or comments about this update? We&apos;d love to{' '}
            <a
              className="text-sky-600 no-underline hover:underline dark:invert"
              rel="noreferrer"
              href="https://docs.google.com/forms/d/e/1FAIpQLScVqiVr3WPIhDIlhSK0adzZsEAIn2ftr_RG614bf7DygHpQpw/viewform?usp=pp_url&entry.1365524899=__other_option__&entry.1365524899.other_option_response=total+energy+change"
            >
              hear your thoughts
            </a>
            !
          </p>
        </div>
      </div>
    </>
  );
}

export default function TotalEnergyIntroModal() {
  const { __ } = useTranslation();
  const [hasTotalEnergyIntroBeenSeen, setHasTotalEnergyIntroBeenSeen] = useAtom(
    hasTotalEnergyIntroBeenSeenAtom
  );
  const [hasOnboardingBeenSeen] = useAtom(hasOnboardingBeenSeenAtom);
  const [searchParameters] = useSearchParams();
  const skipOnboarding = searchParameters.get('skip-onboarding') === 'true';
  // Stop showing this modal a few months after the feature was released
  const isExpired = new Date() > new Date('2023-12-31');

  const visible =
    Boolean(hasOnboardingBeenSeen) &&
    !hasTotalEnergyIntroBeenSeen &&
    !skipOnboarding &&
    !isExpired;

  const handleOpenChange = () => {
    setHasTotalEnergyIntroBeenSeen(true);
  };

  return (
    <Modal
      isOpen={visible}
      setIsOpen={handleOpenChange}
      fullWidth
      testId="total-energy-modal"
    >
      <InfoModalContent />
    </Modal>
  );
}
