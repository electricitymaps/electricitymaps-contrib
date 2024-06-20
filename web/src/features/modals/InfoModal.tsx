import {
  Button,
  FeedbackButton,
  GitHubButton,
  LinkedinButton,
  SlackButton,
  TwitterButton,
} from 'components/Button';
import { VerticalDivider } from 'components/Divider';
import Modal from 'components/Modal';
import { useAtom, useSetAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { FaInfoCircle } from 'react-icons/fa';

import InfoText from './InfoText';
import { isFAQModalOpenAtom, isInfoModalOpenAtom } from './modalAtoms';

const ICON_SIZE = 16;

export function InfoModalContent() {
  const { t } = useTranslation();
  const setIsFAQModalOpen = useSetAtom(isFAQModalOpenAtom);

  return (
    <div className=" flex flex-col items-center ">
      <InfoText />
      <div className="w-[330px] space-y-2 py-2">
        <Button
          size="lg"
          type="secondary"
          onClick={() => setIsFAQModalOpen(true)}
          icon={<FaInfoCircle size={ICON_SIZE} />}
        >
          FAQ
        </Button>
        <FeedbackButton />
        <GitHubButton />
        <TwitterButton />
        <SlackButton />
        <LinkedinButton />
      </div>
      <div className="prose space-x-2  pt-1 text-center text-sm prose-a:text-sky-600 prose-a:no-underline hover:prose-a:underline">
        <a href="https://www.electricitymaps.com/privacy-policy/">
          {t('info.privacy-policy')}
        </a>
        <VerticalDivider />
        <a href="https://www.electricitymaps.com/legal-notice/">
          {t('info.legal-notice')}
        </a>
      </div>
      <p className="text mt-2  text-sm">Version: {APP_VERSION}</p>
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
