import Badge from 'components/Badge';
import { LucideIcon } from 'lucide-react';
import { memo } from 'react';

function EstimationBadge({ text, Icon }: { text?: string; Icon?: LucideIcon }) {
  return text && Icon ? (
    <Badge type={'warning'} icon={<Icon size={12} />} pillText={text} />
  ) : null;
}

export default memo(EstimationBadge);
