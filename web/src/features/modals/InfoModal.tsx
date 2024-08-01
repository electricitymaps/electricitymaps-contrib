import { FAQButton } from 'components/buttons/FAQButton';
import { FeedbackButton } from 'components/buttons/FeedbackButton';
import { GithubButton } from 'components/buttons/GithubButton';
import { LegalNoticeButton } from 'components/buttons/LegalNoticeButton';
import { LinkedinButton } from 'components/buttons/LinkedinButton';
import { PrivacyPolicyButton } from 'components/buttons/PrivacyPolicyButton';
import { SlackButton } from 'components/buttons/SlackButton';
import { VerticalDivider } from 'components/Divider';
import Modal from 'components/Modal';
import { useAtom } from 'jotai';
import { useTranslation } from 'react-i18next';

import InfoText from './InfoText';
import { isInfoModalOpenAtom } from './modalAtoms';

export function InfoModalContent() {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col items-center">
      <InfoText />
      <div className="w-[330px] space-y-2 py-2">
        <FAQButton />
        <FeedbackButton />
        <LinkedinButton />
        <SlackButton />
        <GithubButton />
      </div>
      <div className="flex gap-x-4">
        <PrivacyPolicyButton />
        <VerticalDivider />
        <LegalNoticeButton />
      </div>
      <p className="mt-2">{t('info.version', { version: APP_VERSION })}</p>
    </div>
  );
}

export default function InfoModal() {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useAtom(isInfoModalOpenAtom);

  return (
    <Modal isOpen={isOpen} setIsOpen={setIsOpen} title={t('info.title')}>
      <InfoModalContent />
    </Modal>
  );
}
