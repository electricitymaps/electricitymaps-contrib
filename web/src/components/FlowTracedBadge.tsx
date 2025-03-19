import Badge from 'components/Badge';
import { useAtomValue } from 'jotai';
import { ChevronsUp, TriangleAlert } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { isConsumptionAtom } from 'utils/state/atoms';

import LabelTooltip from './tooltips/LabelTooltip';
import TooltipWrapper from './tooltips/TooltipWrapper';

export default function FlowTracedBadge(): JSX.Element {
  const { t } = useTranslation();
  const isConsumption = useAtomValue(isConsumptionAtom);

  return (
    <TooltipWrapper
      side="bottom"
      tooltipContent={<LabelTooltip>{t('tooltips.flowTraced')}</LabelTooltip>}
    >
      <div>
        <Badge
          pillText={
            isConsumption ? (
              'Flow-traced'
            ) : (
              <p className=" text-xs font-semibold line-through">Flow-traced</p>
            )
          }
          type={isConsumption ? 'success' : 'default'}
          icon={
            isConsumption ? (
              <ChevronsUp className="mr-1 h-4 w-4" />
            ) : (
              <TriangleAlert className="mr-1 h-4 w-4 " />
            )
          }
        />
      </div>
    </TooltipWrapper>
  );
}
