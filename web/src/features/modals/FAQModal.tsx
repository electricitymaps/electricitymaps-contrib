import Modal from 'components/Modal';
import FAQContent from 'features/panels/faq/FAQContent';
import { useAtom } from 'jotai';
import { useTranslation } from 'react-i18next';

import { isFAQModalOpenAtom } from './modalAtoms';

export function FAQModalContent() {
  return (
    <div className="flex flex-col items-center">
      <div className="h-[75vh] overflow-y-scroll">
        <FAQContent />
      </div>
    </div>
  );
}

export default function FAQModal() {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useAtom(isFAQModalOpenAtom);

  return (
    <Modal isOpen={isOpen} setIsOpen={setIsOpen} title={t('misc.faq')}>
      <FAQModalContent />
    </Modal>
  );
}
