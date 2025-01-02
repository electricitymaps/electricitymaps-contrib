import { ApiButton } from 'components/buttons/ApiButton';
import { DocumentationButton } from 'components/buttons/DocumentationButton';
import { FAQButton } from 'components/buttons/FAQButton';
import { FeedbackButton } from 'components/buttons/FeedbackButton';
import { LegalNoticeButton } from 'components/buttons/LegalNoticeButton';
import { LinkedinButton } from 'components/buttons/LinkedinButton';
import { PrivacyPolicyButton } from 'components/buttons/PrivacyPolicyButton';
import Modal from 'components/Modal';
import VerticalDivider from 'components/VerticalDivider';
import { useAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { useRegisterSW } from 'virtual:pwa-register/react';

import InfoText from './InfoText';
import { isInfoModalOpenAtom } from './modalAtoms';

export function InfoModalContent() {
  const { t } = useTranslation();
  const {
    needRefresh: [needRefresh],
    updateServiceWorker,
  } = useRegisterSW();

  const handleUpdate = () => {
    updateServiceWorker(true);
  };

  return (
    <div className="flex flex-col items-center">
      <InfoText />
      <div className="w-[330px] space-y-2 py-2">
        <ApiButton />
        <DocumentationButton />
        <FeedbackButton />
        <LinkedinButton />
        <FAQButton />
      </div>
      <div className="flex gap-x-4">
        <PrivacyPolicyButton />
        <VerticalDivider />
        <LegalNoticeButton />
      </div>
      <div className="mt-2 flex items-center gap-2">
        <p>{t('info.version', { version: APP_VERSION })}</p>
        {needRefresh && (
          <button
            onClick={handleUpdate}
            className="rounded bg-brand-green px-2 py-1 text-xs text-white hover:bg-brand-green/90"
            title={t('updatePrompt.update')}
          >
            {t('updatePrompt.update')}
          </button>
        )}
      </div>
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
