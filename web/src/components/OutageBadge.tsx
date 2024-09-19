import Badge from 'components/Badge';
import { TriangleAlert } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export default function OutageBadge() {
  const { t } = useTranslation();

  return (
    <Badge
      type={'warning'}
      icon={<TriangleAlert size={12} />}
      pillText={t('estimation-badge.outage')}
    />
  );
}
