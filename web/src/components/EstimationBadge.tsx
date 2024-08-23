import Badge from 'components/Badge';
import { TrendingUpDown } from 'lucide-react';

export default function EstimationBadge({ text }: { text: string }) {
  return <Badge type={'warning'} icon={<TrendingUpDown size={16} />} pillText={text} />;
}
