import Badge from 'components/Badge';
import { Asterisk } from 'lucide-react';

export default function EstimationBadge({ text }: { text: string }) {
  return <Badge type={'warning'} icon={<Asterisk size={16} />} pillText={text} />;
}
