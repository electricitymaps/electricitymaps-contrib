import Badge from 'components/Badge';
import { LucideIcon } from 'lucide-react';
import { memo } from 'react';

function EstimationBadge({
  text,
  Icon,
  isPreliminary,
}: {
  text?: string;
  Icon?: LucideIcon;
  isPreliminary?: boolean;
}) {
  return text && Icon ? (
    isPreliminary ? (
      <Badge icon={<Icon size={12} />} pillText={text} />
    ) : (
      <Badge icon={<Icon size={12} />} pillText={text} />
    )
  ) : null;
}

export default memo(EstimationBadge);
