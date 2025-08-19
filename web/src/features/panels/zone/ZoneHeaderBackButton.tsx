import { mapMovingAtom } from 'features/map/mapAtoms';
import { useSetAtom } from 'jotai';
import { ArrowLeft } from 'lucide-react';
import { memo, useCallback } from 'react';
import { useNavigateWithParameters } from 'utils/helpers';

function ZoneHeaderBackButton() {
  const navigate = useNavigateWithParameters();

  const setIsMapMoving = useSetAtom(mapMovingAtom);
  const onNavigateBack = useCallback(() => {
    setIsMapMoving(false);
    navigate({
      to: '/map',
    });
  }, [navigate, setIsMapMoving]);

  return (
    <div
      className="flex min-h-[44px] min-w-[44px] cursor-pointer items-center justify-center self-center p-3 pr-6 text-xl"
      data-testid="left-panel-back-button"
      onClick={onNavigateBack}
      role="button"
      tabIndex={0}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          onNavigateBack();
        }
      }}
    >
      <ArrowLeft />
    </div>
  );
}

export default memo(ZoneHeaderBackButton);
