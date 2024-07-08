import { Button } from 'components/Button';
import Modal from 'components/Modal';
import { useAtom, useSetAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import {
  FaCommentDots,
  FaGithub,
  FaInfoCircle,
  FaSlack,
  FaTwitter,
} from 'react-icons/fa';

import { isFAQModalOpenAtom, isInfoModalOpenAtom } from './modalAtoms';

const ICON_SIZE = 16;

export function InfoModalContent() {
  const { t } = useTranslation();
  const setIsFAQModalOpen = useSetAtom(isFAQModalOpenAtom);

  return (
    <div className="flex flex-col items-center ">
      <div className="prose text-center dark:prose-invert prose-p:my-1 prose-p:leading-snug prose-a:text-sky-600 hover:prose-a:underline">
        <p>{t('info-modal.intro-text')}</p>
        <p
          className=""
          dangerouslySetInnerHTML={{
            __html: t('info-modal.open-source-text', {
              link: 'https://github.com/electricitymaps/electricitymaps-contrib',
              sourcesLink:
                'https://github.com/electricitymaps/electricitymaps-contrib/blob/master/DATA_SOURCES.md#real-time-electricity-data-sources',
            }),
          }}
        />
      </div>
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
          {t('info-modal.feedback-button')}
        </Button>
        <Button
          size="lg"
          type="primary"
          backgroundClasses="bg-gradient-to-r from-[#04275c] to-[#040e23]"
          foregroundClasses="text-white dark:text-white focus-visible:outline-[#04275c]"
          href="https://github.com/electricityMaps/electricitymaps-contrib"
          icon={<FaGithub size={ICON_SIZE} />}
        >
          {t('info-modal.github-button')}
        </Button>
        <Button
          size="lg"
          type="primary"
          backgroundClasses="bg-[#1d9bf0]"
          foregroundClasses="text-white dark:text-white focus-visible:outline-[#1d9bf0]"
          href="https://twitter.com/intent/tweet?url=https://app.electricitymaps.com"
          icon={<FaTwitter size={ICON_SIZE} />}
        >
          {t('info-modal.twitter-button')}
        </Button>
        <Button
          size="lg"
          type="primary"
          backgroundClasses="bg-[#4a154b]"
          foregroundClasses="text-white dark:text-white focus-visible:outline-[#4a154b]"
          href="https://slack.electricitymaps.com/"
          icon={<FaSlack size={ICON_SIZE} />}
        >
          {t('info-modal.slack-button')}
        </Button>
      </div>
      <div className="prose space-x-2  pt-1 text-center text-sm prose-a:text-sky-600 prose-a:no-underline hover:prose-a:underline">
        <a href="https://www.electricitymaps.com/privacy-policy/">
          {t('info-modal.privacy-policy')}
        </a>
        <span className="text-gray-500">|</span>
        <a href="https://www.electricitymaps.com/legal-notice/">
          {t('info-modal.legal-notice')}
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
    <Modal isOpen={isOpen} setIsOpen={setIsOpen} title={t('info-modal.title')}>
      <InfoModalContent />
    </Modal>
  );
}
