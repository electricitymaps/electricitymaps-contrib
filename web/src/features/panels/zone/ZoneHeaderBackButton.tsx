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
      className="self-center py-4 pr-4 text-xl"
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
