import { Button } from 'components/Button';
import Modal from 'components/Modal';
import { useAtom, useSetAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import {
  FaCommentDots,
  FaGithub,
  FaInfoCircle,
  FaLinkedin,
  FaSlack,
  FaTwitter,
} from 'react-icons/fa';

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
        <Button
          size="lg"
          type="primary"
          href="https://forms.gle/VHaeHzXyGodFKZY18"
          icon={<FaCommentDots size={ICON_SIZE} />}
        >
          {t('button.feedback')}
        </Button>
        <Button
          size="lg"
          type="primary"
          backgroundClasses="bg-gradient-to-r from-[#04275c] to-[#040e23]"
          foregroundClasses="text-white dark:text-white focus-visible:outline-[#04275c]"
          href="https://github.com/electricityMaps/electricitymaps-contrib"
          icon={<FaGithub size={ICON_SIZE} />}
        >
          {t('button.github')}
        </Button>
        <Button
          size="lg"
          type="primary"
          backgroundClasses="bg-[#1d9bf0]"
          foregroundClasses="text-white dark:text-white focus-visible:outline-[#1d9bf0]"
          href="https://twitter.com/intent/tweet?url=https://app.electricitymaps.com"
          icon={<FaTwitter size={ICON_SIZE} />}
        >
          {t('button.twitter')}
        </Button>
        <Button
          size="lg"
          type="primary"
          backgroundClasses="bg-[#4a154b]"
          foregroundClasses="text-white dark:text-white focus-visible:outline-[#4a154b]"
          href="https://slack.electricitymaps.com/"
          icon={<FaSlack size={ICON_SIZE} />}
        >
          {t('button.slack')}
        </Button>
        <Button
          size="lg"
          type="primary"
          backgroundClasses="bg-[#0A66C2]"
          foregroundClasses="text-white dark:text-white focus-visible:outline-[#0A66C2]"
          href="https://www.linkedin.com/company/electricitymaps/"
          icon={<FaLinkedin size={ICON_SIZE} />}
        >
          {t('button.linkedin')}
        </Button>
      </div>
      <div className="prose space-x-2  pt-1 text-center text-sm prose-a:text-sky-600 prose-a:no-underline hover:prose-a:underline">
        <a href="https://www.electricitymaps.com/privacy-policy/">
          {t('info.privacy-policy')}
        </a>
        <span className="text-gray-500">|</span>
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
