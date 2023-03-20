import { Button } from 'components/Button';
import Modal from 'components/Modal';
import { useAtom, useSetAtom } from 'jotai';
import {
  FaCommentDots,
  FaGithub,
  FaInfoCircle,
  FaSlack,
  FaTwitter,
} from 'react-icons/fa';
import { useTranslation } from 'translation/translation';
import { isFAQModalOpenAtom, isInfoModalOpenAtom } from './modalAtoms';

const ICON_SIZE = 16;

export function InfoModalContent() {
  const { __ } = useTranslation();
  const setIsFAQModalOpen = useSetAtom(isFAQModalOpenAtom);

  return (
    <div className=" flex flex-col items-center ">
      <div className="prose text-center text-md prose-p:my-1 prose-p:leading-snug prose-a:text-sky-600 hover:prose-a:underline dark:prose-invert">
        <p>{__('info-modal.intro-text')}</p>
        <p
          className=""
          dangerouslySetInnerHTML={{
            __html: __(
              'info-modal.open-source-text',
              'https://github.com/electricitymaps/electricitymaps-contrib',
              'https://github.com/electricitymaps/electricitymaps-contrib/blob/master/DATA_SOURCES.md#real-time-electricity-data-sources'
            ),
          }}
        />
      </div>
      <div>
        <Button
          onClick={() => setIsFAQModalOpen(true)}
          icon={<FaInfoCircle size={ICON_SIZE} />}
        >
          FAQ
        </Button>
        <Button
          background="#44ab60"
          textColor="#fff"
          href="https://forms.gle/VHaeHzXyGodFKZY18"
          icon={<FaCommentDots size={ICON_SIZE} />}
        >
          {__('info-modal.feedback-button')}
        </Button>
        <Button
          background="linear-gradient(to right, #04275c 0%, #040e23 100%)"
          textColor="#fff"
          href="https://github.com/electricityMaps/electricitymaps-contrib"
          icon={<FaGithub size={ICON_SIZE} />}
        >
          {__('info-modal.github-button')}
        </Button>
        <Button
          background="#1d9bf0"
          textColor="#fff"
          href="https://twitter.com/intent/tweet?url=https://app.electricitymaps.com"
          icon={<FaTwitter size={ICON_SIZE} />}
        >
          {__('info-modal.twitter-button')}
        </Button>
        <Button
          background="#4a154b"
          textColor="#fff"
          href="https://slack.electricitymaps.com/"
          icon={<FaSlack size={ICON_SIZE} />}
        >
          {__('info-modal.slack-button')}
        </Button>
      </div>
      <div className="prose space-x-2  pt-1 text-center text-sm prose-a:text-sky-600 prose-a:no-underline hover:prose-a:underline">
        <a href="https://www.electricitymaps.com/privacy-policy/">
          {__('info-modal.privacy-policy')}
        </a>
        <span className="text-gray-500">|</span>
        <a href="https://www.electricitymaps.com/legal-notice/">
          {__('info-modal.legal-notice')}
        </a>
      </div>
      <p className="text mt-2  text-sm">Version: {APP_VERSION}</p>
    </div>
  );
}

export default function InfoModal() {
  const { __ } = useTranslation();
  const [isOpen, setIsOpen] = useAtom(isInfoModalOpenAtom);

  return (
    <Modal isOpen={isOpen} setIsOpen={setIsOpen} title={__('info-modal.title')}>
      <InfoModalContent />
    </Modal>
  );
}
