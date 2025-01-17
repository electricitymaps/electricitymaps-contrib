import { Button } from 'components/Button';
import { isInfoModalOpenAtom, isSettingsModalOpenAtom } from 'features/modals/modalAtoms';
import { useSetAtom } from 'jotai';
import { Info, Settings } from 'lucide-react';

export default function MobileButtons() {
  const setIsInfoModalOpen = useSetAtom(isInfoModalOpenAtom);
  const setIsSettingsModalOpen = useSetAtom(isSettingsModalOpenAtom);

  const handleOpenInfoModal = () => setIsInfoModalOpen(true);
  const handleOpenSettingsModal = () => setIsSettingsModalOpen(true);
  return (
    <div className="flex gap-2 pr-2 pt-2">
      <Button
        size="md"
        type="secondary"
        aria-label="open info modal"
        backgroundClasses="bg-white/80 backdrop-blur dark:bg-gray-800/80 pointer-events-auto"
        onClick={handleOpenInfoModal}
        icon={<Info size={20} />}
      />
      <Button
        size="md"
        type="secondary"
        aria-label="open settings modal"
        onClick={handleOpenSettingsModal}
        backgroundClasses="bg-white/80 backdrop-blur dark:bg-gray-800/80 pointer-events-auto"
        icon={<Settings size={20} />}
        data-testid="settings-button-mobile"
      />
    </div>
  );
}
